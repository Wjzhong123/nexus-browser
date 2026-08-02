import importlib
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("nexus_browser.skills")

_SITE_ADAPTERS = {
    "google": ("nexus_browser.skills.site_adapters.google", "GoogleSearchSkill"),
    "github": ("nexus_browser.skills.site_adapters.github", "GitHubSkill"),
    "wikipedia": ("nexus_browser.skills.site_adapters.wikipedia", "WikipediaSkill"),
    "bilibili": ("nexus_browser.skills.site_adapters.bilibili", "BilibiliSkill"),
    "zhihu": ("nexus_browser.skills.site_adapters.zhihu", "ZhihuSkill"),
    "youtube": ("nexus_browser.skills.site_adapters.youtube", "YouTubeSkill"),
    "xiaohongshu": ("nexus_browser.skills.site_adapters.xiaohongshu", "XiaohongshuSkill"),
    "reddit": ("nexus_browser.skills.site_adapters.reddit", "RedditSkill"),
}


def _lazy_skill(name: str, harness: Any):
    """Import and instantiate a site adapter on first use."""
    module_path, class_name = _SITE_ADAPTERS[name]
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(harness)


class SkillManager:
    """Manages pre-built and dynamically loaded skills.

    Site adapters are imported lazily — only when first accessed — so a
    missing dependency in one adapter won't prevent the server from starting.
    """

    def __init__(self, harness):
        self.harness = harness
        self._skills: Dict[str, Any] = {}

    def _get(self, name: str):
        if name not in self._skills:
            self._skills[name] = _lazy_skill(name, self.harness)
        return self._skills[name]

    async def close(self):
        """Cleanup all lazily-loaded skills."""
        for skill in self._skills.values():
            try:
                await skill.close()
            except Exception:
                pass
        self._skills.clear()

    def get_skill_map(self) -> Dict[str, Callable]:
        """Return a mapping of skill names to their methods for the evolution engine."""
        return {
            "search_google": self._get("google").search,
            "search_github": self._get("github").search_repos,
            "get_github_readme": self._get("github").get_readme,
            "get_wikipedia_summary": self._get("wikipedia").get_summary,
            "search_bilibili": self._get("bilibili").search,
            "search_zhihu": self._get("zhihu").search,
            "get_zhihu_hot": self._get("zhihu").get_hot_list,
            "extract_zhihu_content": self._get("zhihu").extract_content,
            "search_youtube": self._get("youtube").search,
            "search_xiaohongshu": self._get("xiaohongshu").search,
            "open_xiaohongshu": self._get("xiaohongshu").open_home,
            "search_reddit": self._get("reddit").search,
            "get_subreddit": self._get("reddit").get_subreddit_posts,
            "extract_reddit_post": self._get("reddit").extract_post,
            "run_opencli": self.harness.run_opencli,
        }