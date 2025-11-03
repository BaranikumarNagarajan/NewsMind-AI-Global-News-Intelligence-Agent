import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# LangChain / LLM
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.schema import LLMResult
import requests
import json

# -------------------- ENV --------------------
load_dotenv()
PORT = int(os.getenv("PORT", 5000))

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HF_TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "google/flan-t5-base")
USE_OLLAMA = os.getenv("USE_OLLAMA", "False").lower() == "true"

SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", 320))
SUMMARY_TEMPERATURE = float(os.getenv("SUMMARY_TEMPERATURE", 0.4))
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

# -------------------- SEARCHER --------------------
def search_serper(query: str, num_results: int = MAX_SOURCE_LINKS):
    """Search Google via Serper API and return structured results"""
    try:
        url = "https://google.serper.dev/news"
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query, "num": num_results}
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        data = res.json()
        results = []
        for item in data.get("news", [])[:num_results]:
            results.append({
                "title": item.get("title", "Untitled"),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        log.info(f"[searcher] returning {len(results)} items (requested {num_results}).")
        return results
    except Exception as e:
        log.error(f"[searcher] Error: {e}")
        return []

# -------------------- LLM ENGINE --------------------
def generate_summary(question: str, context: str) -> str:
    """Try Groq → HF → fallback"""
    # === try Groq first ===
    if GROQ_API_KEY:
        try:
            log.info(f"[GROQ] model={GROQ_MODEL} tokens={SUMMARY_MAX_TOKENS} temp={SUMMARY_TEMPERATURE}")
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
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

    # === fallback to Hugging Face ===
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
            text = result.generations[0][0].text.strip()
            return text
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

    sources = search_serper(question)
    context = "\n\n".join(
        f"{s['title']}\n{s['snippet'][:MAX_CHARS_PER_SOURCE]}"
        for s in sources
    )

    # ------------------ SMART PROMPT ------------------
    prompt = f"""
You are a precise, neutral news analyst. Use only the articles to answer the user's question.

FORMAT STRICTLY:
- Line 1: A short HEADLINE in Title Case (max 12 words). No punctuation at the end.
- Lines 2–7: 5–6 compact points. Each line begins with ONE UPPERCASE LABEL and " • " then the fact.
  Examples of labels: RESULT, TURNOUT, KEY STATES, TIMELINE, CERTIFICATION, RECOUNT, MARKETS, REACTION, CONTEXT, OUTLOOK
- Each point must be 18–22 words, factual, and dated when possible (e.g., "On Nov 6, ...").
- No extra blank lines, no emojis, no markdown, no tables, no speculation.

TONE:
- Clear, newsroom style. Resolve conflicts by noting timing or source differences.

Question:
{question}

Articles:
{context}

Now write the final answer only following the exact format and length.
""".strip()

    answer = generate_summary(question, prompt)

    # ------------------ LIGHT POST-FORMATTING ------------------
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
    while len(lines) < 6:
        lines.append("OUTLOOK • Additional context may update as outlets refine their reports within the next news cycle.")
    answer = "\n".join(lines)

    return jsonify({"answer": answer, "sources": sources})

# -------------------- STATIC FRONTEND --------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    log.info("🚀 Starting NewsMind (serving frontend from ./static)...")
    app.run(host="0.0.0.0", port=PORT, debug=True)
