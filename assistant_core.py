import asyncio
import httpx
import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import List, Dict

OPENROUTER_API_KEY = os.environ.get("OPEN_ROUTER")
DB_PATH = "assistant_memory.db"
MODEL = "openrouter/free"
FALLBACK_MODEL = "meta-llama/llama-3-8b-instruct:free"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AssistantMemory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def save_message(self, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))

    def get_history(self, limit: int = 10) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT role, content FROM (SELECT * FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id ASC', (limit,)).fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]

async def call_openrouter(messages: List[Dict], model: str = MODEL) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/antigravity-ai", # Required by OpenRouter
        "X-Title": "24/7 AI Assistant",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages
    }

    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=45.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    break
            except Exception as e:
                logger.error(f"Network Error: {str(e)}")
                await asyncio.sleep(5)
    
    # Final fallback if primary model fails
    if model != FALLBACK_MODEL:
        logger.info(f"Retrying with fallback model: {FALLBACK_MODEL}")
        return await call_openrouter(messages, model=FALLBACK_MODEL)
    
    return "Error: Unable to reach AI models after multiple attempts."

async def run_cycle():
    memory = AssistantMemory(DB_PATH)
    
    # 1. Fetch memory
    history = memory.get_history()
    
    # 2. Check for new input (Placeholder for actual trigger logic)
    # In a real app, this would be triggered by a webhook or polling a message queue.
    # For now, we simulate a system pulse or heartbeat.
    prompt = "Conduct a 24/7 system health check and summarize today's environment status."
    
    logger.info("Processing assistant cycle...")
    
    history.append({"role": "user", "content": prompt})
    response = await call_openrouter(history)
    
    # 3. Save to memory
    memory.save_message("user", prompt)
    memory.save_message("assistant", response)
    
    logger.info(f"Assistant Response: {response[:100]}...")

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("ERROR: Please set the OPENROUTER_API_KEY environment variable.")
    else:
        asyncio.run(run_cycle())
