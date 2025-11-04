import os
import requests
from dotenv import load_dotenv

# Load from .env (or searche.py if renamed)
load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("\n🔍 Testing your API keys...\n")

# 1️⃣ SERPER.DEV
if SERPER_API_KEY:
    print("=== Serper.dev ===")
    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": "latest world news", "num": 3}
        r = requests.post("https://google.serper.dev/news", headers=headers, json=payload, timeout=15)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Sample title:", data.get("news", [{}])[0].get("title"))
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("❌ Serper.dev error:", e)
else:
    print("⚠️ SERPER_API_KEY not found in environment")

# 2️⃣ NEWSAPI.ORG
if NEWSAPI_KEY:
    print("\n=== NewsAPI.org ===")
    try:
        r = requests.get(f"https://newsapi.org/v2/everything?q=technology&language=en&pageSize=2&apiKey={NEWSAPI_KEY}", timeout=15)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Sample title:", data.get("articles", [{}])[0].get("title"))
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("❌ NewsAPI error:", e)
else:
    print("⚠️ NEWSAPI_KEY not found in environment")

# 3️⃣ NEWSDATA.IO
if NEWSDATA_KEY:
    print("\n=== NewsData.io ===")
    try:
        r = requests.get(f"https://newsdata.io/api/1/news?apikey={NEWSDATA_KEY}&q=technology&language=en", timeout=15)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Sample title:", data.get("results", [{}])[0].get("title"))
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("❌ NewsData.io error:", e)
else:
    print("⚠️ NEWSDATA_KEY not found in environment")

# 4️⃣ GROQ (summary model)
if GROQ_API_KEY:
    print("\n=== Groq ===")
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Hello!"}]}
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
        print("Status:", r.status_code)
        if r.status_code == 200:
            print("Groq response OK ✅")
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("❌ Groq error:", e)
else:
    print("⚠️ GROQ_API_KEY not found in environment")

print("\n✅ Done! Review the statuses above.\n")
