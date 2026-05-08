from typing import List, Dict, Any
from nexus_browser.skills.base import BaseSkill

class ZhihuSkill(BaseSkill):
    """
    Zhihu Adapter for Search and Answer extraction.
    """
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search questions and answers on Zhihu."""
        url = f"https://www.zhihu.com/search?type=content&q={query}"
        await self.page.goto(url)
        
        # Zhihu often uses 'Search-container' or specific list classes
        await self.page.wait_for_selector(".SearchResult-Card, .ContentItem", timeout=5000)
        
        results = []
        items = await self.page.query_selector_all(".SearchResult-Card, .ContentItem")
        
        for item in items[:8]:
            try:
                title_el = await item.query_selector("h2, .ContentItem-title")
                title = await title_el.inner_text() if title_el else ""
                
                link_el = await item.query_selector("a[data-za-detail-view-element_name='Title'], h2 a")
                link = await link_el.get_attribute("href") if link_el else ""
                if link and link.startswith("//"):
                    link = "https:" + link
                elif link and link.startswith("/"):
                    link = "https://www.zhihu.com" + link
                
                snippet_el = await item.query_selector(".RichText, .SearchItem-snippet")
                snippet = await snippet_el.inner_text() if snippet_el else ""
                
                if title and link:
                    results.append({
                        "title": title.strip(),
                        "url": link,
                        "snippet": snippet.strip()[:200] + "..."
                    })
            except Exception:
                continue
                
        return results
