document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ask-form");
  const input = document.getElementById("query");
  const output = document.getElementById("output");
  const askBtn = document.getElementById("ask-btn");

  const tabs = document.querySelectorAll(".nav-item");
  const grid = document.getElementById("headline-grid");
  const tickerTrack = document.getElementById("ticker-track");
  const lastUpdated = document.getElementById("last-updated");

  const API_BASE = ""; // same-origin backend

  // ---------- Utils ----------
  const escapeHtml = (s="") =>
    s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
     .replace(/\\"/g,"&quot;").replace(/'/g,"&#039;");

  // format summary beautifully
  function formatEnhancedAnswer(answerText = "") {
    const lines = answerText.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (!lines.length) return "";
    const first = `<p>${escapeHtml(lines[0])}</p>`;
    const bullets = lines.slice(1).map(l => {
      const match = l.match(/^([A-Z\s]+)•(.*)$/);
      if (match) {
        const label = match[1].trim();
        const text = match[2].trim();
        return `<div><strong>${escapeHtml(label)}</strong> • ${escapeHtml(text)}</div>`;
      }
      return `<div>${escapeHtml(l)}</div>`;
    }).join("");
    return first + bullets;
  }

  // ---------- Ask ----------
  async function ask(question){
    output.innerHTML = `<p class="hint">⏳ Fetching verified news for: <b>${escapeHtml(question)}</b>...</p>`;
    askBtn.disabled = true;
    try{
      const res = await fetch(`${API_BASE}/ask`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ question })
      });
      const data = await res.json();
      const answer = data?.answer || "No summary available.";
      const sources = Array.isArray(data?.sources) ? data.sources.slice(0,5) : [];

      const srcHtml = sources.map(s =>
        `<li><a href="${s.link}" target="_blank" rel="noopener">${escapeHtml(s.title||s.link)}</a></li>`
      ).join("");

      output.innerHTML = `
        <h3>🧠 AI News Summary</h3>
        <div class="answer">${formatEnhancedAnswer(answer)}</div>
        <h4>🌐 Sources</h4>
        <ul>${srcHtml}</ul>
      `;
    }catch(err){
      output.innerHTML = `<p class="error">⚠️ Network error: ${escapeHtml(err.message)}</p>`;
    }finally{
      askBtn.disabled = false;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if(!q){
      output.innerHTML = `<p class="hint">Type a question to begin.</p>`;
      return;
    }
    ask(q);
  });

  // ---------- Headlines / Ticker ----------
  const topics = {
    home:   "top global news headlines 2025",
    world:  "international politics and conflicts 2025",
    tech:   "latest technology and AI innovation 2025",
    finance:"global finance and economy updates 2025"
  };

  let currentTab = "home";

  function card(link, title, topicKey){
    const remote = `https://source.unsplash.com/400x300/?news,${encodeURIComponent(topicKey)}`;
    const fallback = "anchorwoman.png";
    return `
      <a class="news-card" href="${link}" target="_blank" rel="noopener">
        <img src="${remote}" alt="" onerror="this.onerror=null;this.src='${fallback}'"/>
        <div class="title">${escapeHtml(title || link)}</div>
      </a>
    `;
  }

  function renderTicker(sources){
    if(!Array.isArray(sources) || !sources.length){
      tickerTrack.innerHTML = `<span style="opacity:.7;margin:0 .9rem">No latest headlines.</span>`;
      return;
    }
    tickerTrack.innerHTML = sources
      .map(s => `<a href="${s.link}" target="_blank" rel="noopener">${escapeHtml(s.title || s.link)}</a>`)
      .join(`<span aria-hidden="true"> • </span>`);
  }

  async function loadHeadlines(topicKey="home"){
    grid.innerHTML = `<p class="hint">🔄 Loading ${topicKey} headlines…</p>`;
    try{
      const res = await fetch(`${API_BASE}/ask`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ question: topics[topicKey] })
      });
      const data = await res.json();
      const sources = Array.isArray(data?.sources) ? data.sources.slice(0,6) : [];

      if(!sources.length){
        grid.innerHTML = `<p class="hint">No headlines available right now.</p>`;
        renderTicker([]);
        return;
      }

      grid.innerHTML = sources.map(s => card(s.link, s.title, topicKey)).join("");
      lastUpdated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
      renderTicker(sources);
    }catch(err){
      grid.innerHTML = `<p class="error">⚠️ Failed to load ${topicKey} headlines.</p>`;
      renderTicker([]);
    }
  }

  let refreshTimer = null;
  function startAutoRefresh(){
    if(refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => loadHeadlines(currentTab), 60000);
  }

  tabs.forEach(tab=>{
    tab.addEventListener("click", (e)=>{
      e.preventDefault();
      tabs.forEach(t=>t.classList.remove("active"));
      tab.classList.add("active");

      const cat = tab.dataset.cat;
      if(cat === "about"){
        document.getElementById("about").scrollIntoView({behavior:"smooth"});
        return;
      }
      currentTab = cat;
      loadHeadlines(currentTab);
      startAutoRefresh();
    });
  });

  // Initial load
  loadHeadlines("home");
  startAutoRefresh();
});
