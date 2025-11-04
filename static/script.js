document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ask-form");
  const input = document.getElementById("query");
  const output = document.getElementById("output");
  const askBtn = document.getElementById("ask-btn");
  const summaryInfo = document.getElementById("summary-info");
  const summaryContent = document.getElementById("summary-content");
  const anchorImage = document.getElementById("anchor-image");
  const anchorVideo = document.getElementById("anchor-video");
  const speakingIndicator = document.getElementById("speaking-indicator");
  const latestNewsContainer = document.getElementById("latest-news-container");
  const playButton = document.getElementById("play-button");

  const tabs = document.querySelectorAll(".nav-item");
  const grid = document.getElementById("headline-grid");
  const tickerTrack = document.getElementById("ticker-track");
  const lastUpdated = document.getElementById("last-updated");

  const API_BASE = ""; // same-origin backend

  // Text-to-speech functionality
  let speechSynthesis = window.speechSynthesis;
  let isSpeaking = false;
  let currentUtterance = null;

  // Check if video is available and set up accordingly
  let videoAvailable = false;
  if (anchorVideo) {
    anchorVideo.addEventListener('loadeddata', () => {
      videoAvailable = true;
      anchorVideo.style.display = 'block';
      anchorImage.style.display = 'none';
      console.log("News reporter video loaded successfully");
    });
    
    anchorVideo.addEventListener('error', () => {
      // Fallback to image if video fails to load
      videoAvailable = false;
      anchorVideo.style.display = 'none';
      anchorImage.style.display = 'block';
      console.log("Failed to load news reporter video, using fallback image");
    });
  }

  // ---------- Utility ----------
  const escapeHtml = (s = "") =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
     .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");

  // Format AI summary lines with labels
  function formatEnhancedAnswer(answerText = "") {
    const lines = answerText.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (!lines.length) return "";
    const headline = `<p>${escapeHtml(lines[0])}</p>`;
    const details = lines.slice(1).map(line => {
      const match = line.match(/^([A-Z\s]+)•(.*)$/);
      if (match) {
        const label = match[1].trim();
        const text = match[2].trim();
        return `<div><strong>${escapeHtml(label)}</strong> • ${escapeHtml(text)}</div>`;
      }
      return `<div>${escapeHtml(line)}</div>`;
    }).join("");
    return headline + details;
  }

  // Extract 4-line summary information with better content
  function extractSummaryInfo(answerText = "") {
    const lines = answerText.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    // Skip the first line (headline) and take up to 4 points
    return lines.slice(1, 5).map(line => {
      const match = line.match(/^([A-Z\s]+)•(.*)$/);
      if (match) {
        const label = match[1].trim();
        const text = match[2].trim();
        // Return just the content without the label for a cleaner look
        return text;
      }
      return line;
    });
  }

  // Display 4-line summary information
  function displaySummaryInfo(summaryPoints) {
    if (summaryPoints.length > 0) {
      summaryContent.innerHTML = summaryPoints.map(point => 
        `<div class="summary-point">${escapeHtml(point)}</div>`
      ).join("");
      summaryInfo.style.display = "block";
    } else {
      summaryInfo.style.display = "none";
    }
  }

  // Text-to-speech function with female voice
  function speakText(text) {
    if (!speechSynthesis) return;
    
    // Cancel any ongoing speech
    if (isSpeaking) {
      speechSynthesis.cancel();
      if (videoAvailable && anchorVideo) {
        anchorVideo.pause();
      }
    }
    
    // Create speech utterance
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.lang = 'en-US';
    currentUtterance.rate = 1.0;
    currentUtterance.pitch = 1.2; // Higher pitch for female voice
    
    // Try to get a female voice
    const voices = speechSynthesis.getVoices();
    const femaleVoices = voices.filter(voice => 
      voice.name.includes('Female') || 
      voice.name.includes('Woman') || 
      voice.name.includes('Google UK English Female') ||
      voice.name.includes('Microsoft Zira') ||
      (voice.lang === 'en-US' && voice.name.includes('Samantha'))
    );
    
    if (femaleVoices.length > 0) {
      currentUtterance.voice = femaleVoices[0];
    }
    
    currentUtterance.onstart = () => {
      isSpeaking = true;
      startSpeakingAnimation();
      // Start video if available
      if (videoAvailable && anchorVideo) {
        anchorVideo.currentTime = 0; // Reset to beginning
        anchorVideo.play().catch(e => console.log("Video play error:", e));
      }
    };
    
    currentUtterance.onend = () => {
      isSpeaking = false;
      stopSpeakingAnimation();
      // Pause video if available
      if (videoAvailable && anchorVideo) {
        anchorVideo.pause();
      }
    };
    
    currentUtterance.onerror = () => {
      isSpeaking = false;
      stopSpeakingAnimation();
      // Pause video if available
      if (videoAvailable && anchorVideo) {
        anchorVideo.pause();
      }
    };
    
    speechSynthesis.speak(currentUtterance);
  }

  // Toggle speech playback
  function toggleSpeech(text) {
    if (!speechSynthesis) return;
    
    if (isSpeaking) {
      speechSynthesis.cancel();
      isSpeaking = false;
      stopSpeakingAnimation();
      if (videoAvailable && anchorVideo) {
        anchorVideo.pause();
      }
    } else {
      // Speak the full answer content, not just the headline
      const answerContent = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean).join('. ');
      speakText(answerContent);
    }
  }

  // Animate speaking indicator and anchor image/video
  function startSpeakingAnimation() {
    speakingIndicator.style.display = "flex";
    if (videoAvailable && anchorVideo) {
      anchorVideo.classList.add("speaking");
    } else {
      anchorImage.classList.add("speaking");
    }
  }

  function stopSpeakingAnimation() {
    speakingIndicator.style.display = "none";
    if (videoAvailable && anchorVideo) {
      anchorVideo.classList.remove("speaking");
    } else {
      anchorImage.classList.remove("speaking");
    }
  }

  // Render latest news with images (horizontal layout) - improved image handling
  function renderLatestNews(sources) {
    if (!Array.isArray(sources) || !sources.length) {
      latestNewsContainer.innerHTML = `<p class="hint">No latest news available.</p>`;
      return;
    }
    
    const newsHtml = sources.slice(0, 8).map(source => {
      // Generate more relevant image URLs based on the news content
      let imgUrl;
      const title = source.title || source.link;
      const sourceName = source.source || "Unknown Source";
      
      // Try to get more relevant images based on content with more specific queries
      if (title.toLowerCase().includes('india') || sourceName.toLowerCase().includes('india')) {
        imgUrl = `https://source.unsplash.com/300x200/?india,news,${Math.random()}`;
      } else if (title.toLowerCase().includes('tech') || title.toLowerCase().includes('technology')) {
        imgUrl = `https://source.unsplash.com/300x200/?technology,computer,innovation,${Math.random()}`;
      } else if (title.toLowerCase().includes('finance') || title.toLowerCase().includes('economy')) {
        imgUrl = `https://source.unsplash.com/300x200/?finance,money,business,${Math.random()}`;
      } else if (title.toLowerCase().includes('politics')) {
        imgUrl = `https://source.unsplash.com/300x200/?politics,government,${Math.random()}`;
      } else if (title.toLowerCase().includes('sports')) {
        imgUrl = `https://source.unsplash.com/300x200/?sports,game,competition,${Math.random()}`;
      } else if (title.toLowerCase().includes('health')) {
        imgUrl = `https://source.unsplash.com/300x200/?health,medical,${Math.random()}`;
      } else if (title.toLowerCase().includes('entertainment')) {
        imgUrl = `https://source.unsplash.com/300x200/?entertainment,movie,${Math.random()}`;
      } else if (title.toLowerCase().includes('environment')) {
        imgUrl = `https://source.unsplash.com/300x200/?environment,nature,${Math.random()}`;
      } else if (title.toLowerCase().includes('business')) {
        imgUrl = `https://source.unsplash.com/300x200/?business,corporate,${Math.random()}`;
      } else if (title.toLowerCase().includes('education')) {
        imgUrl = `https://source.unsplash.com/300x200/?education,school,${Math.random()}`;
      } else if (title.toLowerCase().includes('science')) {
        imgUrl = `https://source.unsplash.com/300x200/?science,research,${Math.random()}`;
      } else {
        // Default to general news image with unique identifier to avoid caching
        const keywords = title.split(' ').slice(0, 3).join(',');
        imgUrl = `https://source.unsplash.com/300x200/?news,${encodeURIComponent(keywords)},${Math.random()}`;
      }
      
      // Use news_logo.png as fallback instead of image.png
      const fallback = "news_logo.png";
      
      return `
        <a href="${source.link}" target="_blank" rel="noopener" class="latest-news-item">
          <img src="${imgUrl}" alt="" class="latest-news-image" onerror="this.onerror=null;this.src='${fallback}'"/>
          <div class="latest-news-content">
            <div class="latest-news-title">${escapeHtml(title.substring(0, 70))}${title.length > 70 ? '...' : ''}</div>
            <div class="latest-news-meta">${escapeHtml(sourceName)}</div>
          </div>
        </a>
      `;
    }).join("");
    
    latestNewsContainer.innerHTML = newsHtml;
  }

  // ---------- Ask Function ----------
  async function ask(question) {
    output.innerHTML = `<p class="hint">⏳ Fetching news summary for: <b>${escapeHtml(question)}</b>...</p>`;
    summaryInfo.style.display = "none";
    startSpeakingAnimation();
    askBtn.disabled = true;
    
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      const answer = data?.answer || "No summary available.";
      const sources = Array.isArray(data?.sources) ? data.sources.slice(0, 5) : [];

      const srcHtml = sources.length
        ? sources.map(s =>
            `<li><a href="${s.link}" target="_blank" rel="noopener">${escapeHtml(s.title || s.link)}</a></li>`
          ).join("")
        : "<li><em>No sources found.</em></li>";

      output.innerHTML = `
        <h3>🧠 AI News Summary</h3>
        <div class="answer">${formatEnhancedAnswer(answer)}</div>
        <h4>🌐 Sources</h4>
        <ul>${srcHtml}</ul>
      `;
      
      // Extract and display 4-line summary
      const summaryPoints = extractSummaryInfo(answer);
      displaySummaryInfo(summaryPoints);
      
      // Render latest news
      renderLatestNews(sources);
      
      // Update play button functionality
      playButton.onclick = () => toggleSpeech(answer);
      
      // Scroll to output on mobile for better UX
      if (window.innerWidth <= 720) {
        output.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    } catch (err) {
      output.innerHTML = `<p class="error">⚠️ Network error: ${escapeHtml(err.message)}</p>`;
      summaryInfo.style.display = "none";
      playButton.onclick = null;
    } finally {
      askBtn.disabled = false;
      stopSpeakingAnimation();
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) {
      output.innerHTML = `<p class="hint">Please enter a question.</p>`;
      return;
    }
    ask(q);
  });

  // ---------- Headlines / Ticker ----------
  const topics = {
    home: "top global news headlines today",
    world: "international politics and conflicts today",
    tech: "latest technology and AI innovation today",
    finance: "global finance and economy updates today",
  };

  let currentTab = "home";

  function card(link, title, topicKey) {
    // Generate unique image URLs for headlines as well with more specific queries
    const imgUrl = `https://source.unsplash.com/400x300/?news,${encodeURIComponent(topicKey)},headline,${Math.random()}`;
    // Use news_logo.png as fallback instead of image.png
    const fallback = "news_logo.png";
    return `
      <a class="news-card" href="${link}" target="_blank" rel="noopener">
        <img src="${imgUrl}" alt="" onerror="this.onerror=null;this.src='${fallback}'"/>
        <div class="title">${escapeHtml(title || link)}</div>
      </a>
    `;
  }

  function renderTicker(sources) {
    if (!Array.isArray(sources) || !sources.length) {
      tickerTrack.innerHTML = `<span style="opacity:.7;margin:0 .9rem">No latest headlines available.</span>`;
      return;
    }
    tickerTrack.innerHTML = sources
      .map(s => `<a href="${s.link}" target="_blank" rel="noopener">${escapeHtml(s.title || s.link)}</a>`)
      .join(`<span aria-hidden="true"> • </span>`);
  }

  async function loadHeadlines(topicKey = "home") {
    grid.innerHTML = `<p class="hint">🔄 Loading ${topicKey} headlines…</p>`;
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: topics[topicKey] }),
      });
      const data = await res.json();
      const sources = Array.isArray(data?.sources) ? data.sources.slice(0, 6) : [];
      if (!sources.length) {
        grid.innerHTML = `<p class="hint">No headlines available right now.</p>`;
        renderTicker([]);
        renderLatestNews([]);
        return;
      }
      grid.innerHTML = sources.map(s => card(s.link, s.title, topicKey)).join("");
      lastUpdated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
      renderTicker(sources);
      renderLatestNews(sources);
    } catch (err) {
      grid.innerHTML = `<p class="error">⚠️ Failed to load ${topicKey} headlines.</p>`;
      renderTicker([]);
      renderLatestNews([]);
    }
  }

  // ---------- Tab navigation ----------
  tabs.forEach(tab => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const cat = tab.dataset.cat;
      if (cat === "about") {
        document.getElementById("about").scrollIntoView({ behavior: "smooth" });
        return;
      }
      currentTab = cat;
      loadHeadlines(currentTab);
      startAutoRefresh();
      
      // Scroll to top on mobile for better UX
      if (window.innerWidth <= 720) {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    });
  });

  // ---------- Auto-refresh headlines ----------
  let refreshTimer = null;
  function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => loadHeadlines(currentTab), 60000);
  }

  // Initial load
  loadHeadlines("home");
  startAutoRefresh();
  
  // Handle window resize for responsive behavior
  window.addEventListener("resize", () => {
    // Adjust elements based on screen size if needed
  });
  
  // Load voices when they become available
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => {
      // Voices are now loaded
    };
  }
});