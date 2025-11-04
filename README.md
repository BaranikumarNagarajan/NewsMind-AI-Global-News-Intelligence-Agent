# 🧠 NewsMind AI — Global News Intelligence Agent

**NewsMind AI** is an AI-powered news summarization and aggregation web app built using **LangChain**, **Groq / HuggingFace models**, and a **Flask backend** with a dynamic **HTML + JS frontend**.

It fetches verified news from Google via **Serper API**, summarizes them using **LLMs**, and presents the results with a professional newsroom interface.

---

## 🚀 Features

✅ **Smart News Summaries** — Clean, concise bullet-style summaries with labelled sections (RESULT, TIMELINE, REACTION, etc.)  
✅ **Live News Categories** — Tabs for *Home*, *World*, *Technology*, and *Finance* dynamically refresh headlines  
✅ **Professional Frontend** — Inspired by BBC/CNN design with live ticker, AI anchor image, and red/white palette  
✅ **Real-Time Sources** — Every summary includes verified source links (up to 5)  
✅ **Multi-Model Support** — Works with Groq (`llama-3.1-8b-instant`) or Hugging Face models  
✅ **Single Command Deployment** — Just `python app.py` and visit http://127.0.0.1:5000  

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla JS) |
| **Backend** | Flask (Python 3.10+) |
| **LLM Framework** | LangChain |
| **Search API** | Serper (Google News) |
| **Models** | Groq (LLaMA 3.1 8B Instant) / Hugging Face Transformers |
| **Env Management** | Python-dotenv |

---

## ⚙️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/BaranikumarNagarajan/NewsMind-AI.git
cd NewsMind-AI/backend


```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

```
pip install -r requirements.txt
```

```
# ====== Keys ======
SERPER_API_KEY=your_serper_api_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
HUGGINGFACE_API_KEY=your_huggingface_key

# ====== Summary Settings ======
SUMMARY_MAX_TOKENS=320
SUMMARY_TEMPERATURE=0.4
MAX_SOURCE_LINKS=5
MAX_CHARS_PER_SOURCE=800

# ====== Server ======
PORT=5000
```

```
python app.py
```

| Type    | Example Question                                                     |
| ------- | -------------------------------------------------------------------- |
| Global  | *What’s happening with the U.S. presidential election 2024 results?* |
| India   | *India’s latest AI and technology innovation trends in 2025*         |
| Finance | *How are global markets reacting to the new IMF outlook?*            |
| Tech    | *Recent breakthroughs in artificial intelligence and robotics 2025*  |


🧠 AI Output Example

INDIA’S AI INNOVATION TRENDS IN 2025
RESULT • India’s AI journey aligns with global purpose to confront humanity’s most urgent challenges.
TURNOUT • Unicorn India Ventures Fund III ignites semiconductor and AI innovation in India’s tech ecosystem.
KEY STATES • Ericsson showcases groundbreaking 5G and AI innovations at India Mobile Congress 2025.
TIMELINE • Alphabet to invest $15bn in AI data hub in Andhra Pradesh.
REACTION • Experts emphasize India’s growing role in digital transformation.


🧑‍💻 Creator

BARANI KUMAR NAGARAJAN
📧 nagarajanbaranikumar@gmail.com
 www.linkedin.com/in/baranikumarnagarajan

🔗 GitHub

🌍 Future Roadmap

🔁 Add streaming model support (Ollama local inference)

🕵️ Sentiment analysis on headlines

🧭 Topic-based personalized dashboards

💬 Voice interaction for the AI anchor

🧰 License

MIT License © 2025 Barani Kumar Nagarajan
