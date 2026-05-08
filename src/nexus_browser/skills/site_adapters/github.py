from typing import List, Dict, Any
from nexus_browser.skills.base import BaseSkill

class GitHubSkill(BaseSkill):
    """
    Stable GitHub Adapter using official REST API.
    """
    
    async def search_repos(self, query: str, sort: str = "stars") -> List[Dict[str, Any]]:
        """Search repositories using GitHub API."""
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": "desc",
            "per_page": 5
        }
        
        data = await self.fetch_api(url, params=params)
        
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "full_name": item["full_name"],
                    "description": item["description"],
                    "stars": item["stargazers_count"],
                    "url": item["html_url"],
                    "language": item["language"]
                })
        
        return results

    async def get_readme(self, owner: str, repo: str) -> str:
        """Fetch README content via API."""
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        headers = {"Accept": "application/vnd.github.raw"}
        
        try:
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return "Failed to fetch README."
