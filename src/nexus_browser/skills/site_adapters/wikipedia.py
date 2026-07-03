from nexus_browser.skills.base import BaseSkill

class WikipediaSkill(BaseSkill):
    """
    Wikipedia Adapter using MediaWiki Action API.
    """
    
    async def get_summary(self, title: str) -> str:
        """Get plain-text summary of a Wikipedia article."""
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": title
        }
        
        data = await self.fetch_api(url, params=params)
        
        try:
            pages = data["query"]["pages"]
            # Get the first page entry
            page_id = list(pages.keys())[0]
            if page_id == "-1":
                return "Article not found."
            return pages[page_id]["extract"]
        except Exception:
            return "Failed to fetch Wikipedia summary."
