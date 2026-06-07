import os
import logging
from fastapi import FastAPI, Request
import aiohttp
from duckduckgo_search import AsyncDDGS

# Logger setup for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# API URLs
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "openai/gpt-4o-mini" # OpenRouter-এর একটি ফাস্ট এবং স্মার্ট মডেল

# Conversation History Store (Vercel সার্ভারলেসে এটি সাময়িক, তবে সেশন চলাকালীন কাজ করবে)
USER_HISTORY = {}

# Jarvis System Prompt
SYSTEM_PROMPT = """You are Jarvis, a highly advanced AI Assistant.
Personality: Professional, Helpful, Friendly, and Smart.
Language: You are fluent in both Bengali and English. Always reply in the language the user uses.
Goal: Provide accurate, concise, and helpful answers. If Web Search Context is provided, use it to answer real-time questions."""

# --- Helper Functions ---

async def send_telegram_message(chat_id: int, text: str):
    """Telegram-এ মেসেজ পাঠানোর ফাংশন"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def send_typing_action(chat_id: int):
    """Telegram-এ Typing... অ্যাকশন দেখানোর ফাংশন"""
    url = f"{TELEGRAM_API_URL}/sendChatAction"
    payload = {"chat_id": chat_id, "action": "typing"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def call_openrouter(messages: list) -> str:
    """OpenRouter API কল করার ফাংশন"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/your-repo", # OpenRouter requires this
        "Content-Type": "application/json"
    }
    payload = {
        "model": AI_MODEL,
        "messages": messages
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(OPENROUTER_URL, headers=headers, json=payload) as response:
            data = await response.json()
            try:
                return data['choices'][0]['message']['content']
            except KeyError:
                logger.error(f"OpenRouter Error: {data}")
                return "আমি এই মুহূর্তে কিছু প্রযুক্তিগত সমস্যার সম্মুখীন হচ্ছি।"

async def check_if_search_needed(user_text: str) -> str:
    """ইউজারের মেসেজ চেক করে দেখবে Web Search লাগবে কিনা"""
    check_prompt = f"""Analyze the following message: '{user_text}'.
    If it requires recent news, current weather, sports scores, or facts after your knowledge cutoff, reply strictly with an ideal Web Search Query.
    If no web search is needed, reply EXACTLY with 'NO_SEARCH'."""
    
    messages = [{"role": "user", "content": check_prompt}]
    result = await call_openrouter(messages)
    return result.strip()

async def perform_web_search(query: str) -> str:
    """DuckDuckGo ব্যবহার করে Web Search করার ফাংশন"""
    try:
        async with AsyncDDGS() as ddgs:
            results = await ddgs.atext(query, max_results=3)
            if results:
                formatted_results = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
                return formatted_results
            return "No recent information found."
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return "Search failed."

def get_user_history(chat_id: int) -> list:
    """ইউজারের পূর্বের কনভারসেশন হিস্ট্রি নিয়ে আসার ফাংশন"""
    if chat_id not in USER_HISTORY:
        USER_HISTORY[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return USER_HISTORY[chat_id]

def update_user_history(chat_id: int, history: list):
    """হিস্ট্রি মেমোরি লিমিট ঠিক রাখার ফাংশন (সর্বোচ্চ ১০টি মেসেজ)"""
    if len(history) > 11:
        # System prompt (index 0) রেখে শেষের ১০টি মেসেজ সেভ করবে
        USER_HISTORY[chat_id] = [history[0]] + history[-10:]
    else:
        USER_HISTORY[chat_id] = history

# --- Main Webhook Route ---

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Telegram থেকে আসা Webhook Request হ্যান্ডেল করার মূল পয়েন্ট"""
    try:
        update = await request.json()
        
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            user_name = message["from"].get("first_name", "User")

            # Ignore empty or non-text messages
            if not text:
                return {"status": "ignored"}

            # Handle Commands
            if text == "/start":
                welcome_msg = f"Hello {user_name}! আমি Jarvis, আপনার পার্সোনাল AI Assistant। যেকোনো প্রশ্ন করতে পারেন, আমি সাহায্য করার জন্য প্রস্তুত।"
                await send_telegram_message(chat_id, welcome_msg)
                return {"status": "ok"}
            
            if text == "/help":
                help_msg = "আমি বাংলা এবং ইংরেজি দুই ভাষাতেই কথা বলতে পারি। সাম্প্রতিক খবর বা সাধারণ যেকোনো বিষয়ে আমাকে প্রশ্ন করতে পারেন।"
                await send_telegram_message(chat_id, help_msg)
                return {"status": "ok"}

            # 1. Show Typing Action
            await send_typing_action(chat_id)

            # 2. Check if Web Search is needed
            search_query = await check_if_search_needed(text)
            search_context = ""
            
            if search_query and search_query != "NO_SEARCH":
                logger.info(f"Performing Web Search for: {search_query}")
                search_results = await perform_web_search(search_query)
                search_context = f"\n\n[System Note: Below is fresh web search context for '{search_query}'. Use it to answer if relevant.]\n{search_results}"

            # 3. Manage History & Build Prompt
            history = get_user_history(chat_id)
            user_content = text + search_context
            history.append({"role": "user", "content": user_content})

            # 4. Get Final Answer from AI
            reply = await call_openrouter(history)

            # 5. Save AI reply to history
            # Remove search context from the user's prompt in history so it doesn't bloat future turns
            history[-1]["content"] = text 
            history.append({"role": "assistant", "content": reply})
            update_user_history(chat_id, history)

            # 6. Send Reply to User
            await send_telegram_message(chat_id, reply)

    except Exception as e:
        logger.error(f"Webhook Error: {e}")
    
    # Telegram requires an HTTP 200 response quickly
    return {"status": "ok"}
  
