import asyncio
import httpx
import sqlite3
import os
import json
import logging
import yfinance as yf
from datetime import datetime
from typing import List, Dict

# Configuration
OPENROUTER_API_KEY = os.environ.get("OPEN_ROUTER")
DB_PATH = "assistant_memory.db"
MODEL = "openrouter/free"
FALLBACK_MODEL = "meta-llama/llama-3-8b-instruct:free"

class SovereignSelfHealLoop:
    """The Alpha Directive: Sense -> Diagnose -> Heal -> Act."""
    def __init__(self, memory: 'AssistantMemory'):
        self.memory = memory
        self.entropy_level = 0

    async def sense(self, error: Exception, context: str):
        logger.error(f"Sense: Detected entropy increase in {context}: {str(error)}")
        self.entropy_level += 1
        return await self.diagnose(error, context)

    async def diagnose(self, error: Exception, context: str):
        logger.info(f"Diagnose: Analyzing root cause of {type(error).__name__}")
        # Simplistic diagnostic: Network vs Logic vs API
        if isinstance(error, httpx.NetworkError):
            return "network_failure"
        elif "429" in str(error):
            return "rate_limit"
        return "unknown_entropy"

    async def heal(self, diagnosis: str):
        logger.info(f"Heal: Attempting metabolic recovery for {diagnosis}")
        if diagnosis == "network_failure":
            await asyncio.sleep(10) # Simple recovery
            return True
        elif diagnosis == "rate_limit":
            await asyncio.sleep(60)
            return True
        return False

    def log_metabolism(self, action: str, result: str):
        self.memory.save_message("system_metabolism", f"Action: {action} | Result: {result} | Entropy: {self.entropy_level}")

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

def get_market_data() -> str:
    """Fetch latest financial data for key assets."""
    assets = {
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
        "Bitcoin": "BTC-USD",
        "Gold": "GC=F",
        "HSI": "^HSI"
    }
    
    report = "【实时金融行情汇报】\n"
    for name, symbol in assets.items():
        try:
            ticker = yf.Ticker(symbol)
            # Use fast_info or history for reliable cloud fetching
            data = ticker.history(period="1d")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                prev_close = data['Open'].iloc[-1]
                change = ((current_price - prev_close) / prev_close) * 100
                report += f"- {name}: ${current_price:.2f} ({change:+.2f}%)\n"
            else:
                report += f"- {name}: 数据获取失败\n"
        except Exception as e:
            report += f"- {name}: 错误 {str(e)}\n"
    return report

async def call_openrouter(messages: List[Dict], model: str = MODEL) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/antigravity-ai",
        "X-Title": "24/7 AI Financial Assistant",
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
    
    if model != FALLBACK_MODEL:
        return await call_openrouter(messages, model=FALLBACK_MODEL)
    
    return "Error: Unable to reach AI models."

async def run_cycle():
    if not OPENROUTER_API_KEY:
        logger.error("OPEN_ROUTER environment variable is missing.")
        return

    memory = AssistantMemory(DB_PATH)
    healer = SovereignSelfHealLoop(memory)
    
    try:
        # 1. Fetch Market Data
        logger.info("Fetching market data...")
        market_report = get_market_data()
        
        # 2. Prepare Context
        history = memory.get_history()
        system_prompt = (
            "你是一个24小时运行的专业金融助理。你现在的任务是分析最新的市场行情，"
            "并结合历史对话为用户提供简练、专业的洞察。请使用中文回答。"
        )
        
        full_prompt = f"{market_report}\n\n基于以上行情，请给出你的简要分析和今日建议。"
        
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": full_prompt}]
        
        # 3. Call AI
        logger.info("Calling OpenRouter with market report...")
        response = await call_openrouter(messages)
        
        # 4. Save to memory
        memory.save_message("user", "System Pulse: Get Financial Report")
        memory.save_message("assistant", f"{market_report}\n\n{response}")
        
        healer.log_metabolism("Cycle Execution", "Success")
        logger.info("Cycle complete. Memory updated.")

        # 5. Export to JSON for GitHub Pages
        export_data = {
            "market_report": market_report,
            "ai_insight": response,
            "last_update": datetime.now().isoformat(),
            "entropy": healer.entropy_level
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        logger.info("data.json exported for dashboard.")

    except Exception as e:
        diagnosis = await healer.sense(e, "Main Cycle")
        recovered = await healer.heal(diagnosis)
        if recovered:
            logger.info("Self-healing successful, retrying cycle...")
            await run_cycle()
        else:
            healer.log_metabolism("Cycle Execution", f"Failed: {str(e)}")
            logger.error("Critical failure: Entropy exceeded recovery capacity.")

if __name__ == "__main__":
    asyncio.run(run_cycle())
