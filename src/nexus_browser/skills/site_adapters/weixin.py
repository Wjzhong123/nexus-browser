import logging
from typing import Any, Dict, List

from nexus_browser.skills.base import BaseSkill

logger = logging.getLogger("nexus_browser.skills")


class WeixinSkill(BaseSkill):
    """
    WeChat Official Account (微信公众号) Adapter.

    Uses OpenCLI's `weixin` adapter for structured search without login walls.
    This is the only reliable way to search public WeChat articles.
    """

    async def search(self, query: str, public: bool = True) -> List[Dict[str, Any]]:
        """Search WeChat Official Account articles.

        Args:
            query: Search keywords.
            public: Whether to limit to public (non-login) search results.

        Returns:
            List of article dicts with title / url / snippet / publish_time.
        """
        kwargs: Dict[str, Any] = {"limit": 10}
        if public:
            kwargs["public"] = True

        result = await self.harness.run_opencli(
            "weixin", "search", [query], kwargs
        )
        if result.get("status") == "error":
            logger.error("Weixin search failed: %s", result.get("message"))
            return []

        raw = result.get("result", [])
        if isinstance(raw, str):
            # Fallback: return raw text if not JSON
            return [{"title": raw[:500], "raw": True}]

        articles = []
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            articles.append({
                "title": item.get("title", ""),
                "url": item.get("url", item.get("link", "")),
                "snippet": item.get("snippet", item.get("summary", "")),
                "publish_time": item.get("publish_time", item.get("date", "")),
                "author": item.get("author", item.get("account", "")),
            })
        return articles

    async def get_hot_list(self) -> List[Dict[str, Any]]:
        """WeChat doesn't expose a public trending list via OpenCLI."""
        return []