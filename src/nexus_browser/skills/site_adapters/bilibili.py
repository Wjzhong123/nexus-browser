from typing import List, Dict, Any
from nexus_browser.skills.base import BaseSkill

class BilibiliSkill(BaseSkill):
    """
    Bilibili Adapter for Search and Metadata extraction.
    """
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search videos on Bilibili."""
        # Use the web interface
        url = f"https://search.bilibili.com/all?keyword={query}"
        await self.page.goto(url)
        
        # Wait for results to load (B站 results are often in div.video-list)
        await self.page.wait_for_selector(".video-list-item, .bili-video-card", timeout=5000)
        
        results = []
        # Find video cards
        cards = await self.page.query_selector_all(".video-list-item, .bili-video-card")
        
        for card in cards[:10]: # Limit to top 10
            try:
                title_el = await card.query_selector("h3, .v-img + div a, .bili-video-card__info--tit")
                title = await title_el.get_attribute("title") or await title_el.inner_text() if title_el else ""
                
                link_el = await card.query_selector("a")
                link = await link_el.get_attribute("href") if link_el else ""
                if link and link.startswith("//"):
                    link = "https:" + link
                
                # Get stats (views, date, etc)
                stats_el = await card.query_selector(".video-card__info--bottom, .bili-video-card__stats")
                stats = await stats_el.inner_text() if stats_el else ""
                
                if title and link:
                    results.append({
                        "title": title.strip(),
                        "url": link,
                        "stats": stats.strip().replace("\n", " ")
                    })
            except Exception:
                continue
                
        return results
