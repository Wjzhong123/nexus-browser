import logging
from .site_adapters.google import GoogleSearchSkill
from .site_adapters.github import GitHubSkill
from .site_adapters.wikipedia import WikipediaSkill
from .site_adapters.bilibili import BilibiliSkill
from .site_adapters.zhihu import ZhihuSkill
from .site_adapters.youtube import YouTubeSkill

logger = logging.getLogger("nexus_browser.skills")

class SkillManager:
    """Manages pre-built and dynamically loaded skills."""
    
    def __init__(self, harness):
        self.harness = harness
        # Initialize built-in skills
        self.google = GoogleSearchSkill(harness)
        self.github = GitHubSkill(harness)
        self.wikipedia = WikipediaSkill(harness)
        self.bilibili = BilibiliSkill(harness)
        self.zhihu = ZhihuSkill(harness)
        self.youtube = YouTubeSkill(harness)
        
    async def close(self):
        """Cleanup all skills."""
        await self.google.close()
        await self.github.close()
        await self.wikipedia.close()
        await self.bilibili.close()
        await self.zhihu.close()
        await self.youtube.close()

    def get_skill_map(self):
        """Return a mapping of skill names to their methods for the evolution engine."""
        return {
            "search_google": self.google.search,
            "search_github": self.github.search_repos,
            "get_github_readme": self.github.get_readme,
            "get_wikipedia_summary": self.wikipedia.get_summary,
            "search_bilibili": self.bilibili.search,
            "search_zhihu": self.zhihu.search,
            "search_youtube": self.youtube.search,
        }
