import os
import requests
import logging

logger = logging.getLogger("newsmind")

# Load API keys from environment or .env file
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")  # backup option
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY")  # another backup

def fetch_news(query: str, num_results: int = 5):
    """
    Fetches news results for a given query.
    Tries Serper.dev first, then falls back to NewsAPI.org or NewsData.io.
    """

    results = []

    # -------------------------------
    # 1️⃣ Try Serper.dev
    # -------------------------------
    if SERPER_API_KEY:
        try:
            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {"q": query, "num": num_results}
            logger.info("[searcher] Fetching from Serper.dev...")
            resp = requests.post(
                "https://google.serper.dev/news",
                headers=headers,
                json=payload,
                timeout=25
            )
            resp.raise_for_status()
            data = resp.json()

            if "news" in data and len(data["news"]) > 0:
                results = [
                    {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "source": item.get("source"),
                    }
                    for item in data["news"][:num_results]
                ]
                logger.info(f"[searcher] Got {len(results)} items from Serper.dev")
                return results
            else:
                logger.warning("[searcher] No news found from Serper.dev")

        except Exception as e:
            logger.error(f"[searcher] Serper.dev failed: {e}")

    # -------------------------------
    # 2️⃣ Try NewsAPI.org (Backup)
    # -------------------------------
    if NEWSAPI_KEY:
        try:
            url = f"https://newsapi.org/v2/everything?q={query}&pageSize={num_results}&language=en&apiKey={NEWSAPI_KEY}"
            logger.info("[searcher] Fetching from NewsAPI.org...")
            resp = requests.get(url, timeout=20)
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
                logger.info(f"[searcher] Got {len(results)} items from NewsAPI.org")
                return results
            else:
                logger.warning("[searcher] No articles found in NewsAPI.org response")

        except Exception as e:
            logger.error(f"[searcher] NewsAPI.org failed: {e}")

    # -------------------------------
    # 3️⃣ Try NewsData.io (Final Fallback)
    # -------------------------------
    if NEWSDATA_KEY:
        try:
            url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_KEY}&q={query}&language=en"
            logger.info("[searcher] Fetching from NewsData.io...")
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            if "results" in data:
                results = [
                    {
                        "title": a.get("title"),
                        "link": a.get("link"),
                        "snippet": a.get("description"),
                        "source": a.get("source_id"),
                    }
                    for a in data["results"][:num_results]
                ]
                logger.info(f"[searcher] Got {len(results)} items from NewsData.io")
                return results
            else:
                logger.warning("[searcher] No results from NewsData.io")

        except Exception as e:
            logger.error(f"[searcher] NewsData.io failed: {e}")

    # -------------------------------
    # 4️⃣ If all fail, return an empty list
    # -------------------------------
    logger.error("[searcher] All news sources failed — returning empty list.")
    return results
