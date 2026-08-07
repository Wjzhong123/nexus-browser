# Nexus Browser 🚀

The Ultimate AI-Native Browser & App Control Harness.

Nexus Browser combines the best of **OpenHarness** (Visualization), **Browser-Harness** (Self-healing), and **OpenCLI** (Stability & Session Reuse).

## 🌟 The "AI Search Supplement" Mission
Nexus Browser is designed to be the perfect companion to traditional AI Search (e.g., Perplexity, Google Search). It fills the "blind spots" that standard crawlers cannot reach.

### 4 Killer Advantages for AI Search:
1.  **Breaking the "Login Wall"**: Unlike standard bots, Nexus Browser uses **your real browser session**. It can access your private GitHub repos, Zhihu's deep answers, and WeChat Official Accounts that are hidden from public search engines.
2.  **Rich Media & Community Wisdom**: Directly search **Bilibili, YouTube, Reddit, and Xiaohongshu**. It brings "human-lived experience" into the AI's knowledge base, not just official news.
3.  **Interactive & Live**: Standard search is static. Nexus Browser is **active**. It can click "Expand More", navigate complex UI filters, and handle real-time interactions to find the most current data.
4.  **Desktop Integration**: It bridges the gap between Web and Desktop. Find a solution on StackOverflow and immediately apply it inside your **Cursor** or **VS Code** via CDP attachment.

## Key Features
- **System-Wide Automation**: Control Web Browsers and **Electron Desktop Apps**.
- **Self-Healing (Dynamic Evolution)**: Agents can write and hot-reload their own Python "Skills".
- **OpenCLI Native Integration**: Natively supports 800+ deterministic site adapters from the OpenCLI ecosystem.
- **Session Transparency**: Zero-login required by attaching to your live browser.
- **Web Task Routing** 🆕: Just describe what you want in natural language ("看看知乎热搜", "搜B站AI视频"), and the router automatically selects the best data source between OpenCLI and browser.
- **Cached Chromium Launch** 🆕: Avoids Playwright download stalls by using local cached Chrome for Testing.

## Quick Start
```bash
# Install
pip install nexus-browser

# Start the server
nexus-browser
```

### Quick Start (Development)
```bash
# Clone the repo
git clone https://github.com/Wjzhong123/nexus-browser.git
cd nexus-browser

# Install dependencies
pip install -e ".[dev]"
playwright install chromium

# Start the server
python -m nexus_browser.main
```

## API Endpoints

### 🔄 Unified Web Task Routing (`POST /web_task`)
The primary entry point. Just describe what you want:

```json
// Request
{
  "task": "看看知乎今天的热搜",
  "site": null,     // optional: force a site name
  "intent": null,   // optional: force an intent (hot/search/detail/news)
  "query": null     // optional: explicit search keywords
}

// Response (via OpenCLI)
{
  "status": "success",
  "result": {
    "output": "路由: opencli(zhihu → hot)\n\n知乎热榜数据...",
    "is_error": false,
    "method": "opencli(zhihu → hot)"
  }
}
```

**What it handles:**
- `"看看知乎热搜"` → `opencli(zhihu → hot)` — trending list
- `"搜一下B站上的AI视频"` → `opencli(bilibili → search)` — search results
- `"在github上找langchain"` → `opencli(github → search)` — repo search
- `"打开 https://example.com"` → `browser_control` — page navigation
- `"搜索公众号文章，主题是AI创业"` → `opencli(weixin → search)` — WeChat articles

### Other Endpoints
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| POST | `/attach` | Attach to a running browser/Electron app via CDP |
| GET | `/pages` | List all open tabs/windows |
| GET | `/status` | Server status, registered skills, and routes |
| POST | `/execute` | Execute a registered skill by name |
| POST | `/evolve` | Hot-reload agent-written helper code |
| POST | `/web_task` | Unified natural-language task routing 🆕 |

## Architecture

```
User Task (e.g., "看看知乎热搜")
    │
    ▼
┌─────────────────────────────────┐
│      Web Task Router            │
│  (router.py / POST /web_task)   │
│                                 │
│  1. resolve_site(task)          │
│     → aliases, URLs, site names │
│  2. resolve_intent(task)        │
│     → hot / search / detail     │
│  3. extract_query(task)         │
│     → auto-extract keywords     │
└──────────┬──────────────────────┘
           │
    ┌──────┴──────┐
    ▼              ▼
OpenCLI        Browser
(151+ sites)   (CDP-attached)
```
