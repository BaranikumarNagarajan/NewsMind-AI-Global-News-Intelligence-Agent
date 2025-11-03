import os
import logging
import requests
from duckduckgo_search import DDGS

log = logging.getLogger("newsmind.search")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def _serper_news(query, num_results=5):
    if not SERPER_API_KEY:
        log.info("SERPER_API_KEY missing; skipping Serper.")
        return []
    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": num_results}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return [
            {
                "title": i.get("title"),
                "link": i.get("link"),
                "snippet": i.get("snippet", ""),
                "date": i.get("date") or i.get("publishedDate"),
                "source": i.get("source") or i.get("publisher"),
            }
            for i in data.get("news", [])
        ]
    except Exception as e:
        log.warning(f"Serper error: {e}")
        return []

def _ddg_news(query, num_results=5):
    try:
        results = []
        with DDGS() as ddgs:
            for h in ddgs.news(query, max_results=num_results):
                results.append({
                    "title": h.get("title"),
                    "link": h.get("url"),
                    "snippet": h.get("body", ""),
                    "date": h.get("date"),
                    "source": h.get("source"),
                })
        return results
    except Exception as e:
        log.warning(f"DuckDuckGo error: {e}")
        return []

def _dedupe(items):
    seen = set(); out = []
    for i in items:
        url = (i.get("link") or "").split("?")[0]
        if url and url not in seen:
            seen.add(url); out.append(i)
    return out

def search_news(query, num_results=5):
    s = _serper_news(query, num_results)
    need = max(0, num_results - len(s))
    d = _ddg_news(query, need) if need else []
    out = _dedupe(s + d)[:num_results]
    log.info(f"[search] returning {len(out)} items (requested {num_results}).")
    return out
