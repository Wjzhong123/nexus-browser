from typing import List, Dict, Any
from .base import BaseSkill

class XiaohongshuSkill(BaseSkill):
    """
    Xiaohongshu Adapter for Search and Content extraction.
    """
    
    async def open_home(self):
        """Open Xiaohongshu homepage."""
        await self.page.goto("https://www.xiaohongshu.com")
        return "Opened Xiaohongshu home."

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search notes on Xiaohongshu."""
        url = f"https://www.xiaohongshu.com/search_result?keyword={query}"
        await self.page.goto(url)
        
        # Xiaohongshu results are in a feed
        await self.page.wait_for_selector(".note-item, .feeds-container", timeout=8000)
        
        results = []
        items = await self.page.query_selector_all(".note-item")
        
        for item in items[:10]:
            try:
                title_el = await item.query_selector(".title, .footer .name")
                title = await title_el.inner_text() if title_el else "Note"
                
                link_el = await item.query_selector("a")
                link = await link_el.get_attribute("href") if link_el else ""
                if link and link.startswith("/"):
                    link = "https://www.xiaohongshu.com" + link
                
                author_el = await item.query_selector(".author .name")
                author = await author_el.inner_text() if author_el else ""
                
                if link:
                    results.append({
                        "title": title.strip(),
                        "url": link,
                        "author": author.strip()
                    })
            except Exception:
                continue
                
        return results
