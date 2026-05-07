import logging
from .site_adapters.google import GoogleSearchSkill
from .site_adapters.github import GitHubSkill
from .site_adapters.wikipedia import WikipediaSkill

logger = logging.getLogger("nexus_browser.skills")

class SkillManager:
    """Manages pre-built and dynamically loaded skills."""
    
    def __init__(self, harness):
        self.harness = harness
        # Initialize built-in skills
        self.google = GoogleSearchSkill(harness)
        self.github = GitHubSkill(harness)
        self.wikipedia = WikipediaSkill(harness)
        
    async def close(self):
        """Cleanup all skills."""
        await self.google.close()
        await self.github.close()
        await self.wikipedia.close()

    def get_skill_map(self):
        """Return a mapping of skill names to their methods for the evolution engine."""
        return {
            "search_google": self.google.search,
            "search_github": self.github.search_repos,
            "get_github_readme": self.github.get_readme,
            "get_wikipedia_summary": self.wikipedia.get_summary,
        }
