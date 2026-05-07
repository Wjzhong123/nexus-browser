from typing import List, Dict, Any
from .base import BaseSkill

class YouTubeSkill(BaseSkill):
    """
    YouTube Adapter for Search and Metadata.
    """
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search videos on YouTube."""
        url = f"https://www.youtube.com/results?search_query={query}"
        await self.page.goto(url)
        
        # Wait for video renderers
        await self.page.wait_for_selector("ytd-video-renderer", timeout=5000)
        
        results = []
        renderers = await self.page.query_selector_all("ytd-video-renderer")
        
        for renderer in renderers[:10]:
            try:
                title_el = await renderer.query_selector("#video-title")
                title = await title_el.get_attribute("title") or await title_el.inner_text()
                link = await title_el.get_attribute("href")
                if link:
                    link = "https://www.youtube.com" + link
                
                meta_el = await renderer.query_selector("#metadata-line")
                meta = await meta_el.inner_text() if meta_el else ""
                
                if title and link:
                    results.append({
                        "title": title.strip(),
                        "url": link,
                        "metadata": meta.strip().replace("\n", " • ")
                    })
            except Exception:
                continue
                
        return results
