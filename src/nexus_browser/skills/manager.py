import logging
from nexus_browser.skills.site_adapters.google import GoogleSearchSkill
from nexus_browser.skills.site_adapters.github import GitHubSkill
from nexus_browser.skills.site_adapters.wikipedia import WikipediaSkill
from nexus_browser.skills.site_adapters.bilibili import BilibiliSkill
from nexus_browser.skills.site_adapters.zhihu import ZhihuSkill
from nexus_browser.skills.site_adapters.youtube import YouTubeSkill
from nexus_browser.skills.site_adapters.xiaohongshu import XiaohongshuSkill

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
        self.xiaohongshu = XiaohongshuSkill(harness)
        
    async def close(self):
        """Cleanup all skills."""
        await self.google.close()
        await self.github.close()
        await self.wikipedia.close()
        await self.bilibili.close()
        await self.zhihu.close()
        await self.youtube.close()
        await self.xiaohongshu.close()

    def get_skill_map(self):
        """Return a mapping of skill names to their methods for the evolution engine."""
        return {
            "search_google": self.google.search,
            "search_github": self.github.search_repos,
            "get_github_readme": self.github.get_readme,
            "get_wikipedia_summary": self.wikipedia.get_summary,
            "search_bilibili": self.bilibili.search,
            "search_zhihu": self.zhihu.search,
            "get_zhihu_hot": self.zhihu.get_hot_list,
            "extract_zhihu_content": self.zhihu.extract_content,
            "search_youtube": self.youtube.search,
            "search_xiaohongshu": self.xiaohongshu.search,
            "open_xiaohongshu": self.xiaohongshu.open_home,
        }
