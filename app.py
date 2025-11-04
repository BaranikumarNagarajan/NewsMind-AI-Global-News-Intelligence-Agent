import os
import logging
import requests
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# LangChain / LLM
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.schema import LLMResult

# -------------------- ENV --------------------
load_dotenv()
PORT = int(os.getenv("PORT", 5000))

# API KEYS
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HF_TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "google/flan-t5-base")

USE_OLLAMA = os.getenv("USE_OLLAMA", "False").lower() == "true"
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", 450))
SUMMARY_TEMPERATURE = float(os.getenv("SUMMARY_TEMPERATURE", 0.3))
MAX_SOURCE_LINKS = int(os.getenv("MAX_SOURCE_LINKS", 5))
MAX_CHARS_PER_SOURCE = int(os.getenv("MAX_CHARS_PER_SOURCE", 800))

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s:newsmind:%(message)s")
log = logging.getLogger("newsmind")

# -------------------- APP --------------------
app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)

log.info("--------------------------------------------------")
log.info("Frontend served from ./static (same-origin).")
log.info(f"🧩 SUMMARY_MAX_TOKENS={SUMMARY_MAX_TOKENS} TEMP={SUMMARY_TEMPERATURE}")
log.info(f"🔗 MAX_SOURCE_LINKS={MAX_SOURCE_LINKS} MAX_CHARS_PER_SOURCE={MAX_CHARS_PER_SOURCE}")
log.info("--------------------------------------------------")

# -------------------- NEWS FETCHER --------------------
def fetch_news(query: str, num_results: int = MAX_SOURCE_LINKS):
    results = []

    # --- Try Serper.dev ---
    if SERPER_API_KEY:
        try:
            headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
            payload = {"q": query, "num": num_results}
            log.info("[searcher] Fetching from Serper.dev...")
            resp = requests.post("https://google.serper.dev/news", headers=headers, json=payload, timeout=25)
            resp.raise_for_status()
            data = resp.json()

            if "news" in data:
                results = [
                    {
                        "title": n.get("title"),
                        "link": n.get("link"),
                        "snippet": n.get("snippet"),
                        "source": n.get("source"),
                    }
                    for n in data["news"][:num_results]
                ]
                log.info(f"[searcher] Got {len(results)} items from Serper.dev")
                return results
        except Exception as e:
            log.error(f"[searcher] Serper.dev failed: {e}")

    # --- Try NewsAPI.org ---
    if NEWSAPI_KEY:
        try:
            log.info("[searcher] Fetching from NewsAPI.org...")
            url = f"https://newsapi.org/v2/everything?q={query}&pageSize={num_results}&language=en&apiKey={NEWSAPI_KEY}"
            resp = requests.get(url, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            if "articles" in data:
                results = [
                    {
                        "title": a.get("title"),
                        "link": a.get("url"),
                        "snippet": a.get("description"),
                        "source": a.get("source", {}).get("name"),
                    }
                    for a in data["articles"][:num_results]
                ]
                log.info(f"[searcher] Got {len(results)} items from NewsAPI.org")
                return results
        except Exception as e:
            log.error(f"[searcher] NewsAPI.org failed: {e}")

    # --- Try NewsData.io ---
    if NEWSDATA_KEY:
        try:
            log.info("[searcher] Fetching from NewsData.io...")
            url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_KEY}&q={query}&language=en"
            resp = requests.get(url, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            if "results" in data:
                results = [
                    {
                        "title": r.get("title"),
                        "link": r.get("link"),
                        "snippet": r.get("description"),
                        "source": r.get("source_id"),
                    }
                    for r in data["results"][:num_results]
                ]
                log.info(f"[searcher] Got {len(results)} items from NewsData.io")
                return results
        except Exception as e:
            log.error(f"[searcher] NewsData.io failed: {e}")

    log.error("[searcher] All news sources failed — returning empty list.")
    return results

# -------------------- LLM ENGINE --------------------
def generate_summary(question: str, context: str) -> str:
    if GROQ_API_KEY:
        try:
            log.info(f"[GROQ] model={GROQ_MODEL} tokens={SUMMARY_MAX_TOKENS} temp={SUMMARY_TEMPERATURE}")
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": context}],
                "temperature": SUMMARY_TEMPERATURE,
                "max_tokens": SUMMARY_MAX_TOKENS,
            }
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            log.warning(f"⚠️ Groq generation error: {e}")

    if HUGGINGFACE_API_KEY:
        try:
            log.info(f"[HF] model={HF_TEXT_MODEL} tokens={SUMMARY_MAX_TOKENS} temp={SUMMARY_TEMPERATURE}")
            llm = HuggingFaceHub(
                repo_id=HF_TEXT_MODEL,
                huggingfacehub_api_token=HUGGINGFACE_API_KEY,
                model_kwargs={"temperature": SUMMARY_TEMPERATURE, "max_new_tokens": SUMMARY_MAX_TOKENS},
            )
            prompt = PromptTemplate.from_template("{context}")
            result: LLMResult = llm.generate(prompts=[prompt.format(context=context)])
            return result.generations[0][0].text.strip()
        except Exception as e:
            log.warning(f"⚠️ HuggingFace generation error: {e}")

    return "⚠️ No generation backend available (set GROQ_API_KEY or HUGGINGFACE_API_KEY)."

# -------------------- API --------------------
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    log.info(f"[Q] “{question}”")

    if not question:
        return jsonify({"answer": "Please provide a question.", "sources": []})

    sources = fetch_news(question, num_results=MAX_SOURCE_LINKS)
    context = "\n\n".join(f"{s['title']}\n{s['snippet'][:MAX_CHARS_PER_SOURCE]}" for s in sources)

    prompt = f"""
You are a precise, neutral news analyst. Use only the articles to answer the user's question with detailed explanations.

FORMAT STRICTLY:
- Line 1: A short HEADLINE in Title Case (max 12 words)
- Lines 2-5: 4 detailed explanation points with specific facts, figures, and context
- Each point must start with a descriptive category in UPPERCASE followed by • and then a detailed explanation (2-3 sentences with specific data)
- No emojis, markdown, or speculation
- Focus on concrete details, statistics, specific information, and comprehensive explanations rather than generic statements
- Include actual numbers, percentages, dates, and specific names when available

Question:
{question}

Articles:
{context}
""".strip()

    answer = generate_summary(question, prompt)

    def _title_case(s: str) -> str:
        small = {"and","or","the","of","to","in","on","for","a","an","at","by","vs"}
        words = s.split()
        out = []
        for i,w in enumerate(words):
            lw = w.lower()
            if i!=0 and lw in small:
                out.append(lw)
            else:
                out.append(w[:1].upper()+w[1:])
        return " ".join(out)

    lines = [ln.strip() for ln in (answer or "").splitlines() if ln.strip()]
    if lines:
        lines[0] = _title_case(lines[0].rstrip("."))
    while len(lines) < 5:
        lines.append("OUTLOOK • Additional context may update as outlets refine reports within the next cycle. Developments in this area continue to evolve, with stakeholders monitoring key indicators for further insights. Market participants are advised to stay informed about regulatory changes and technological advancements. Future updates will provide more clarity on emerging trends and their potential impacts.")
    answer = "\n".join(lines)

    return jsonify({"answer": answer, "sources": sources})

# -------------------- STATIC FRONTEND --------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    static_folder = app.static_folder or "static"
    if path and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    return send_from_directory(static_folder, "index.html")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    log.info("🚀 Starting NewsMind (serving frontend from ./static)...")
    app.run(host="0.0.0.0", port=PORT, debug=True)