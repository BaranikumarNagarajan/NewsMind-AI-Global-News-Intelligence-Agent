import os
import logging
import requests

log = logging.getLogger("newsmind.llm")
logging.basicConfig(level=logging.INFO)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def _call_groq(prompt: str, max_tokens: int, temperature: float):
    if not GROQ_API_KEY:
        return 401, {"error": "No GROQ_API_KEY set."}
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=120)
        return r.status_code, (r.json() if r.content else {})
    except Exception as e:
        log.exception("Groq request failed")
        return 500, {"error": str(e)}

def _extract_text(data):
    try:
        if isinstance(data, dict) and "choices" in data and data["choices"]:
            msg = data["choices"][0].get("message", {})
            return (msg.get("content") or data["choices"][0].get("text") or "").strip()
    except Exception:
        pass
    return ""

def generate_summary(prompt: str, *, max_new_tokens: int = 320, temperature: float = 0.4) -> str:
    log.info(f"[GROQ] model={GROQ_MODEL} tokens={max_new_tokens} temp={temperature}")
    status, data = _call_groq(prompt, max_new_tokens, temperature)
    if status == 200:
        txt = _extract_text(data)
        if txt:
            return txt
        log.warning("Groq returned 200 but no text field.")
        return "⚠️ Groq returned an empty response."
    err = data.get("error") if isinstance(data, dict) else str(data)
    log.warning(f"Groq error {status}: {err}")
    return f"⚠️ Groq generation error ({status}): {err}"
