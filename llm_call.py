import os
import httpx
import logging
import json
import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('127.0.0.1')

url = "https://openrouter.ai/api/v1/chat/completions"

api_key = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

prompt = """
You are a helpful assistant. 
Your function is to work over each function call and help according to th need of the function.
"""
async def call_llm(prompt:str):
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt} ],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        result = response.json()
        return result