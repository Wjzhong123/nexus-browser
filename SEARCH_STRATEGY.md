# Nexus Browser: Dual-Search Orchestration Strategy 🧠

This document outlines how AI Agents should coordinate between **Traditional AI Search** and **Nexus Browser** to provide the most comprehensive answers.

## 0. The Unified Entry Point: Web Task Router 🆕

**Before using any specific tool, agents should first try the `web_task` endpoint.**

```python
# Instead of writing:
result = await harness.run_opencli("zhihu", "hot")
# or:
result = await harness.navigate_and_get("https://www.zhihu.com/billboard")

# Just describe the task:
result = await route_task(harness, "看看知乎今天的热搜")
```

The router automatically:
1. Parses the site name (151+ aliases, Chinese/English, URL hosts)
2. Resolves the intent (hot / search / detail / news)
3. Extracts search keywords from the task description
4. Routes to the best data source (OpenCLI → browser → fallback)

### Router Decision Tree

```
User Task Description
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Site Resolution                  │
│    ├─ URL host (https://example.com)│
│    ├─ Chinese alias (知乎 → zhihu)  │
│    └─ OpenCLI site name (bilibili)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Intent Resolution                │
│    ├─ "热搜"/"排行" → hot           │
│    ├─ "搜索"/"找" → search          │
│    ├─ "详情"/"内容" → detail        │
│    └─ "新闻"/"资讯" → news          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Query Extraction (if search)     │
│    "搜一下B站上的AI视频" → "AI视频" │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Route Decision                   │
│    ├─ Site in OpenCLI list → opencli│
│    ├─ Has URL/interactive keywords  │
│    │  → browser_control             │
│    └─ No site/URL → suggest search  │
└─────────────────────────────────────┘
```

## 1. The Search Matrix

| Scenario | Traditional AI Search | Nexus Browser |
| :--- | :--- | :--- |
| Official Documentation | ✅ Primary Source | ❌ Overhead |
| General News | ✅ Fast & Wide | ❌ Redundant |
| **Real User Experience** | ❌ Often missed | ✅ **Superior (Zhihu, Reddit, X)** |
| **Login-Protected Content** | ❌ Blocked | ✅ **Only Way (GitHub, WeChat)** |
| **Interactive Pages** | ❌ Can't click/filter | ✅ **Interactive Control** |
| **Desktop App Context** | ❌ Browser-only | ✅ **Full System Access** |

## 2. Implementation: The "Observer-Refiner" Pattern

To ensure a comprehensive search, the Agent should follow this 2-step process:

### Step 1: Broad Observation (Traditional)
Use tools like `google_search` or `web_search` to map the landscape.
- **Goal**: Understand terminology, get dates, and find authoritative links.

### Step 2: Deep Refinement (Nexus Browser)
If the initial results are "thin" or "generic", trigger Nexus Browser.
- **Trigger A**: "I see the solution is on a forum (e.g., V2EX or Reddit), let me go in and check the comments for pitfalls."
- **Trigger B**: "I found a relevant video on Bilibili, let me check the metadata/top comments for more context."
- **Trigger C**: "The answer requires me to check my private project structure on GitHub."

## 3. System Prompt Template

Add the following to your Agent's system instructions:

```markdown
### Universal Search Protocol
When asked a complex question:
1. First, use `traditional_search` to get the 'Standard Answer'.
2. IMMEDIATELY check if Nexus Browser can add value by:
   - Searching social communities (Zhihu/Bilibili/Reddit) for "human perspective".
   - Accessing your private context (GitHub/Notion).
   - Performing interactive actions (clicking "Show More" on dynamic sites).
3. Synthesize both sources: Point out where the official docs and real-world experience differ.
```

## 4. Verification
A successful search is one where the Agent says:
> "According to the official docs (Search A), this feature is supported. However, I checked the latest user discussions on Zhihu (Nexus Browser), and many users report a specific bug when using it with Docker. Here is the workaround I found..."
