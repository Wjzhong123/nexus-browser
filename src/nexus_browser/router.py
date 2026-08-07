"""
Unified web task router (web_task) for Nexus Browser.

Users describe a task in natural language (e.g. "看看知乎热搜"), and the router
automatically selects the best data source:
  1. OpenCLI (151+ sites, structured data, fastest, no login needed)
  2. Browser-based sites (via CDP-attached browser)
  3. Web search fallback (for unknown/information retrieval tasks)
"""

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger("nexus_browser.router")

# ── OpenCLI 151+ site list (synced with opencli list) ──
OPENCLI_SITES = [
    "12306", "1688", "1point3acres", "36kr", "51job", "aibase", "amazon", "antigravity",
    "arxiv", "band", "barchart", "bbc", "bilibili", "binance", "bloomberg", "bluesky",
    "booking", "boss", "brave", "chaoxing", "chatgpt", "chatwise", "chess", "claude",
    "cnki", "codex", "coingecko", "confluence", "coupang", "crates", "ctrip", "cursor",
    "dblp", "deepseek", "defillama", "devto", "dianping", "dictionary", "dockerhub",
    "douban", "doubao", "douyin", "duckduckgo", "eastmoney", "endoflife", "facebook",
    "flathub", "flomo", "gemini", "geogebra", "gitee", "github", "google", "goproxy",
    "grok", "hackernews", "hf", "homebrew", "huodongxing", "hupu", "imdb", "indeed",
    "instagram", "jd", "jianyu", "jike", "jimeng", "jira", "ke", "kimi", "lesswrong",
    "lichess", "linkedin", "lobsters", "maimai", "manus", "maven", "mdn", "medium",
    "mubu", "notebooklm", "nowcoder", "npm", "nuget", "nvd", "oeis", "ones",
    "openalex", "openfda", "openreview", "osv", "packagist", "paperreview", "pixiv",
    "powerchina", "producthunt", "pubmed", "pypi", "qoder", "quark", "qwen", "reddit",
    "rednote", "reuters", "rfc", "rubygems", "sinablog", "sinafinance", "slock",
    "smzdm", "spotify", "stackoverflow", "steam", "substack", "suno", "taobao", "tdx",
    "ths", "tieba", "tiktok", "toutiao", "tvmaze", "twitter", "uisdc", "uiverse",
    "upwork", "v2ex", "wanfang", "web", "weibo", "weixin", "weread", "wikidata",
    "wikipedia", "wttr", "xianyu", "xiaoe", "xiaohongshu", "xiaoyuzhou", "xueqiu",
    "yahoo", "yollomi", "youdao", "youtube", "yuanbao", "zhihu", "zlibrary", "zsxq",
]

# ── Chinese aliases → OpenCLI site name ──
SITE_ALIASES = {
    "知乎": "zhihu", "b站": "bilibili", "哔哩哔哩": "bilibili", "bilibili": "bilibili",
    "抖音": "douyin", "微博": "weibo", "小红书": "xiaohongshu", "rednote": "xiaohongshu",
    "豆瓣": "douban", "贴吧": "tieba", "头条": "toutiao", "虎扑": "hupu",
    "雪球": "xueqiu", "京东": "jd", "淘宝": "taobao", "闲鱼": "xianyu",
    "github": "github", "推特": "twitter", "油管": "youtube", "优兔": "youtube",
    "stack overflow": "stackoverflow", "产品猎人": "producthunt", "黑客新闻": "hackernews",
    "维基百科": "wikipedia", "维基": "wikipedia", "大众点评": "dianping",
    "脉脉": "maimai", "即刻": "jike", "微信": "weixin", "公众号": "weixin",
    "得到": "weixin", "知识星球": "zsxq", "网易云": "netease",
    "c站": "claude", "gpt": "chatgpt", "红迪": "reddit", "x": "twitter",
    "科技美妆": "aibase", "亚马逊": "amazon", "谷歌": "google", "bing": "google",
    "币安": "binance", "steam": "steam", "npm": "npm", "pypi": "pypi",
    "crates": "crates", "huggingface": "hf", "hugging face": "hf", "arxiv": "arxiv",
    "学术": "arxiv", "论文": "paperreview", "医学": "pubmed", "处方": "pubmed",
    "法律": "rfc", "docker": "dockerhub", "crates.io": "crates",
}

# ── Intent keywords → OpenCLI subcommand ──
INTENT_MAP: dict[str, list[str]] = {
    "hot": ["hot", "热榜", "热搜", "热门", "排行", "top", "trending", "热门话题", "今日热点"],
    "search": ["search", "搜索", "搜", "查找", "查询", "找一下", "查一下", "找找", "找", "search for"],
    "detail": ["detail", "详情", "内容", "信息", "question", "article", "thread", "item", "info", "post"],
    "news": ["news", "新闻", "资讯", "最新"],
}


def resolve_site(task: str) -> Optional[str]:
    """Parse target site name from a task description.

    Priority: URL host > Chinese alias > OpenCLI site name.
    """
    lowered = task.lower()
    # 0. URL host first (avoid 'x' in example.com matching twitter alias)
    if "://" in lowered or "www." in lowered:
        m = re.search(r"https?://(?:www\.)?([a-z0-9-]+)\.", lowered)
        if m:
            host = m.group(1)
            for site in OPENCLI_SITES:
                if site in host:
                    return site
            return host  # Not in OpenCLI list, return as-is (router will use browser)
    # 1. Alias exact match (Chinese / English)
    for alias, site in SITE_ALIASES.items():
        if alias.lower() in lowered:
            return site
    # 2. OpenCLI site name exact match
    for site in OPENCLI_SITES:
        if site.lower() in lowered:
            return site
    return None


def resolve_intent(task: str) -> str:
    """Parse user intent from a task description."""
    lowered = task.lower()
    for intent, keywords in INTENT_MAP.items():
        for kw in keywords:
            if kw.lower() in lowered:
                return intent
    return "detail"


def extract_query(task: str, intent: str, explicit_query: Optional[str] = None) -> Optional[str]:
    """Extract search keywords from a task description.

    Priority:
    1. Explicit query parameter
    2. Auto-extract from task text when intent is 'search'
    """
    if explicit_query:
        return explicit_query

    if intent != "search":
        return None

    lowered = task.lower()
    # Search keywords extraction (by priority)
    search_markers = ["搜索", "搜一下", "搜", "查找", "查询", "找一下", "找找", "找"]
    for marker in search_markers:
        idx = lowered.find(marker)
        if idx >= 0:
            after = task[idx + len(marker):].strip().lstrip("，,的 ：:")
            break
    else:
        after = task

    # Clean: remove known site names
    for alias in SITE_ALIASES:
        after = re.sub(re.escape(alias), "", after, flags=re.IGNORECASE)
    for site in OPENCLI_SITES:
        after = re.sub(re.escape(site), "", after, flags=re.IGNORECASE)

    # Clean extra whitespace and punctuation
    after = re.sub(r"[，,。.！!？?、：:;；\s]+", " ", after).strip()
    # Remove known noise words
    noise = ["文章", "内容", "主题", "信息", "关于", "有关", "的", "什么", "哪些",
             "怎么", "如何", "看看", "一下", "今天", "最新", "热门", "上的", "中的",
             "是的", "是"]
    for word in noise:
        after = after.replace(word, " ")
    after = re.sub(r"\s+", " ", after).strip()

    return after if after else None


async def route_opencli(
    harness: Any,
    site: str,
    intent: str,
    query: Optional[str],
    limit: int = 5,
) -> dict:
    """Route a task to OpenCLI via the harness.

    Returns a dict with keys: output, is_error, method.
    """
    # Map intent to subcommand
    if intent == "hot":
        subcommand = "hot"
    elif intent == "news":
        subcommand = "news"
    elif intent == "search":
        subcommand = "search"
    else:
        subcommand = "detail"

    args_list: list[str] = []
    kwargs: dict[str, Any] = {"limit": limit}
    if query:
        args_list.append(query)

    result = await harness.run_opencli(site, subcommand, args_list, kwargs)

    if result.get("status") == "error":
        # Fallback: try hot (most sites have it)
        if subcommand != "hot":
            fallback = await harness.run_opencli(site, "hot", [], {"limit": limit})
            if fallback.get("status") != "error":
                return {
                    "output": f"路由: opencli({site} → {subcommand} 失败，回退 hot)\n\n{fallback.get('result', fallback.get('message', ''))}",
                    "is_error": False,
                    "method": f"opencli({site} → hot, fallback)",
                }
        err = result.get("message", str(result))[:400]
        return {
            "output": (
                f"路由: opencli({site} → {subcommand}) 失败。\n"
                f"错误: {err}\n"
                f"提示: 站点 '{site}' 可能不支持 '{subcommand}' 子命令，"
                f"或该操作需要登录。可尝试：\n"
                f"  1. 换一种说法（如 '{site} 热门' → hot）\n"
                f"  2. 提供具体 URL 用 browser_control 打开\n"
                f"  3. 若需登录态操作，先确认浏览器已登录 {site}"
            ),
            "is_error": False,
            "method": f"opencli({site} → {subcommand})",
        }

    output = result.get("result", result.get("message", ""))
    return {
        "output": f"路由: opencli({site} → {subcommand})\n\n{output}",
        "is_error": False,
        "method": f"opencli({site} → {subcommand})",
    }


async def route_browser(
    harness: Any,
    task: str,
    query: Optional[str],
) -> dict:
    """Route a task to the browser for interactive/web-based tasks.

    Returns a dict with keys: output, is_error, method.
    """
    from nexus_browser.app_harness import RouteResult

    # Determine target URL
    target_url = None
    if query and query.startswith("http"):
        target_url = query
    else:
        m = re.search(r"https?://\S+", task)
        if m:
            target_url = m.group(0).rstrip(".,;:!?")

    if target_url:
        result = await harness.navigate_and_get(target_url)
    else:
        # No URL: use Google search
        import urllib.parse
        q = query or task
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
        result = await harness.navigate_and_get(search_url)

    if isinstance(result, RouteResult):
        return {
            "output": result.output,
            "is_error": result.is_error,
            "method": "browser_control",
        }
    return {
        "output": str(result),
        "is_error": False,
        "method": "browser_control",
    }


async def route_task(
    harness: Any,
    task: str,
    site: Optional[str] = None,
    intent: Optional[str] = None,
    query: Optional[str] = None,
) -> dict:
    """Unified task routing: parse task → route to best data source.

    Args:
        harness: AppHarness instance.
        task: Natural language task description.
        site: Optional explicit site name override.
        intent: Optional explicit intent override.
        query: Optional explicit search query override.

    Returns:
        dict with keys: output, is_error, method
    """
    # 1. Parse site and intent
    resolved_site = site or resolve_site(task)
    resolved_intent = intent or resolve_intent(task)

    # 2. Extract query
    resolved_query = extract_query(task, resolved_intent, query)

    # 3. Route decision
    if resolved_site and resolved_site in OPENCLI_SITES:
        return await route_opencli(harness, resolved_site, resolved_intent, resolved_query)

    # 4. Site not in OpenCLI: check if URL or interactive keywords present
    if "://" in task or any(kw in task.lower() for kw in ("打开", "访问", "点击", "登录", "滚动", "输入")):
        return await route_browser(harness, task, resolved_query)

    # 5. Pure information retrieval (no site, no URL)
    return {
        "output": (
            f"无法从任务中解析出明确站点。已解析站点: {resolved_site or '无'}，意图: {resolved_intent}。\n"
            f"建议：\n"
            f"  - 明确站点名（如 '看看知乎热搜'）→ opencli 自动路由\n"
            f"  - 提供 URL（如 '打开 https://example.com'）→ 浏览器操作\n"
            f"  - 全网检索 → 使用 web_search 搜索工具"
        ),
        "is_error": False,
        "method": "fallback",
    }