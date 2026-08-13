"""
ADRE CLI entry point.

Runs the raw-reality intake pipeline over any dataset:
    input file -> text -> claim extraction -> belief states -> review/revert.

Supports plain text, markdown, CSV, JSON, and JSONL inputs. Results are
printed to the console and optionally written to a CSV or JSON report.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from belief_manager import refresh_belief
from belief_reviewer import review_belief
from claim_extraction import extract_claims, extract_claims_llm_sync
from revert_decision import should_revert

SUPPORTED_EXTENSIONS = {".txt", ".md", ".text", ".csv", ".json", ".jsonl", ".ndjson"}

REPORT_COLUMNS = [
    "state_id",
    "claim",
    "claim_type",
    "status",
    "confidence",
    "uncertainty",
    "contradiction_count",
    "source_diversity",
    "verification_count",
    "decay_rate",
    "refresh",
    "reverify",
    "downgrade",
    "revert",
    "review_reason",
]


def _configure_stdout() -> None:
    """
    Ensures the console can print unicode claim text on Windows.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def read_dataset(path: Path) -> List[str]:
    """
    Reads a dataset file into a list of text chunks regardless of format.

    Each CSV cell, JSON string value, or JSONL record becomes its own chunk
    so short or unpunctuated fragments are still evaluated as claims.
    """
    suffix = path.suffix.lower()

    if suffix in {".csv"}:
        return _read_csv(path)
    if suffix in {".json"}:
        return _read_json(path)
    if suffix in {".jsonl", ".ndjson"}:
        return _read_jsonl(path)

    return [path.read_text(encoding="utf-8", errors="replace")]


def _read_csv(path: Path) -> List[str]:
    """
    Returns each non-empty CSV cell value as its own text chunk.
    """
    chunks: List[str] = []
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.reader(handle):
            chunks.extend(cell.strip() for cell in row if cell and cell.strip())
    return chunks


def _collect_strings(value: Any, sink: List[str]) -> None:
    """
    Recursively harvests every string value from nested JSON structures.
    """
    if isinstance(value, str):
        if value.strip():
            sink.append(value.strip())
    elif isinstance(value, dict):
        for item in value.values():
            _collect_strings(item, sink)
    elif isinstance(value, list):
        for item in value:
            _collect_strings(item, sink)
    elif value is not None:
        sink.append(str(value))


def _read_json(path: Path) -> List[str]:
    """
    Returns each string value from an arbitrary JSON document as a chunk.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    sink: List[str] = []
    _collect_strings(data, sink)
    return sink


def _read_jsonl(path: Path) -> List[str]:
    """
    Returns each string value from newline-delimited JSON records as a chunk.
    """
    sink: List[str] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                sink.append(line.strip())
                continue
            _collect_strings(record, sink)
    return sink


def build_report(belief) -> Dict[str, Any]:
    """
    Runs one refresh cycle plus review/revert on a belief and returns a row.
    """
    refresh_belief(belief)

    review = review_belief(belief)
    revert = should_revert(belief)

    reasons = list(review["reason"])
    reasons.extend(revert["reason"])

    return {
        "state_id": belief.state_id,
        "claim": belief.claim,
        "claim_type": belief.claim_type.value,
        "status": belief.status,
        "confidence": round(belief.confidence, 4),
        "uncertainty": round(belief.uncertainty, 4),
        "contradiction_count": belief.contradiction_count,
        "source_diversity": round(belief.source_diversity, 4),
        "verification_count": belief.verification_count,
        "decay_rate": belief.decay_rate,
        "refresh": review["refresh"],
        "reverify": review["reverify"],
        "downgrade": review["downgrade"],
        "revert": revert["revert"],
        "review_reason": "; ".join(reasons),
    }


def write_csv_report(path: Path, rows: List[Dict[str, Any]]) -> None:
    """
    Writes the belief report to a CSV file.
    """
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_json_report(path: Path, rows: List[Dict[str, Any]]) -> None:
    """
    Writes the belief report to a JSON file.
    """
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False)


def run_pipeline(
    text_chunks: List[str],
    source_id: str,
    source_type: str,
    use_llm: bool = False,
) -> List[Dict[str, Any]]:
    """
    Runs the full ADRE pipeline over dataset chunks and returns report rows.
    """
    rows: List[Dict[str, Any]] = []
    next_state_id = 0

    for chunk in text_chunks:
        if use_llm:
            beliefs = extract_claims_llm_sync(
                chunk, source_id, source_type, start_state_id=next_state_id
            )
        else:
            beliefs = extract_claims(
                chunk, source_id, source_type, start_state_id=next_state_id
            )
        rows.extend(build_report(belief) for belief in beliefs)
        next_state_id += len(beliefs)

    return rows


def summarize(rows: List[Dict[str, Any]]) -> None:
    """
    Prints a compact status summary of extracted beliefs.
    """
    if not rows:
        print("No claims extracted from the dataset.")
        return

    print(f"\nExtracted {len(rows)} claims.\n")
    rank_counts: Dict[str, int] = {}
    for row in rows:
        rank_counts[row["status"]] = rank_counts.get(row["status"], 0) + 1

    for status in sorted(rank_counts):
        print(f"  {status}: {rank_counts[status]}")

    degraded = [row for row in rows if row["downgrade"] or row["revert"]]
    if degraded:
        print(f"\n{len(degraded)} belief(s) flagged for downgrade/revert:")
        for row in degraded:
            print(f"  [{row['state_id']}] {row['claim'][:60]} -> {row['review_reason']}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Autonomous Data Reality Engine - dataset evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Supported inputs: .txt, .md, .text, .csv, .json, .jsonl, .ndjson\n"
            "Example: python main.py --input data/report.csv --output results.json --source-type news"
        ),
    )
    parser.add_argument("--input", "-i", type=Path, help="path to the dataset file")
    parser.add_argument(
        "--text",
        "-t",
        help="inline text to process instead of a file (mutually exclusive with --input)",
    )
    parser.add_argument("--output", "-o", type=Path, help="save report as .csv or .json")
    parser.add_argument("--source-id", default="dataset", help="source identifier")
    parser.add_argument("--source-type", default="untrusted", help="source type (e.g. news, api)")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="use LLM-assisted claim extraction (requires OPENROUTER_API_KEY)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    _configure_stdout()
    args = parse_args(argv)

    if args.input and args.text:
        print("error: --input and --text are mutually exclusive.", file=sys.stderr)
        return 2

    if not args.input and not args.text:
        print("error: provide --input <file> or --text <inline text>.", file=sys.stderr)
        return 2

    if args.input:
        if not args.input.is_file():
            print(f"error: file not found: {args.input}", file=sys.stderr)
            return 2
        if args.input.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(
                f"error: unsupported dataset format '{args.input.suffix}'. "
                f"Supported: {sorted(SUPPORTED_EXTENSIONS)}",
                file=sys.stderr,
            )
            return 2
        chunks = read_dataset(args.input)
        text = " ".join(chunks)
        print(f"Loaded dataset: {args.input} ({len(chunks)} chunks, {len(text)} chars)")
    else:
        chunks = [args.text]

    rows = run_pipeline(
        text_chunks=chunks,
        source_id=args.source_id,
        source_type=args.source_type,
        use_llm=args.llm,
    )

    summarize(rows)

    if args.output:
        if args.output.suffix.lower() == ".csv":
            write_csv_report(args.output, rows)
        elif args.output.suffix.lower() == ".json":
            write_json_report(args.output, rows)
        else:
            print(f"error: unsupported output format '{args.output.suffix}'.", file=sys.stderr)
            return 2
        print(f"\nReport saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())