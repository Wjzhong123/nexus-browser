from typing import List, Dict, Any, Optional
from nexus_browser.skills.base import BaseSkill

class ZhihuSkill(BaseSkill):
    """
    Zhihu Adapter for Search and Answer extraction.
    """
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search questions and answers on Zhihu."""
        url = f"https://www.zhihu.com/search?type=content&q={query}"
        await self.page.goto(url)
        await self.page.wait_for_selector(".SearchResult-Card, .ContentItem", timeout=5000)
        
        results = []
        items = await self.page.query_selector_all(".SearchResult-Card, .ContentItem")
        for item in items[:8]:
            try:
                title_el = await item.query_selector("h2, .ContentItem-title")
                title = await title_el.inner_text() if title_el else ""
                link_el = await item.query_selector("a[data-za-detail-view-element_name='Title'], h2 a")
                link = await link_el.get_attribute("href") if link_el else ""
                if link and link.startswith("//"): link = "https:" + link
                elif link and link.startswith("/"): link = "https://www.zhihu.com" + link
                snippet_el = await item.query_selector(".RichText, .SearchItem-snippet")
                snippet = await snippet_el.inner_text() if snippet_el else ""
                if title and link:
                    results.append({"title": title.strip(), "url": link, "snippet": snippet.strip()[:200] + "..."})
            except Exception: continue
        return results

    async def get_hot_list(self) -> List[Dict[str, Any]]:
        """Get the current trending/hot list from Zhihu."""
        # billboard URL is more stable and bypasses login wall
        urls = ["https://www.zhihu.com/billboard", "https://www.zhihu.com/hot"]
        
        for url in urls:
            try:
                logger.info(f"Navigating to Zhihu Hot via {url}...")
                await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
                # Wait for the item container
                await self.page.wait_for_selector(".HotItem, .HotList-item", timeout=10000)
                
                items = await self.page.query_selector_all(".HotItem, .HotList-item")
                if not items:
                    continue
                    
                results = []
                for item in items[:20]:
                    try:
                        rank_el = await item.query_selector(".HotItem-index, .HotList-itemIndex")
                        rank = await rank_el.inner_text() if rank_el else ""
                        
                        title_el = await item.query_selector(".HotItem-title, .HotList-itemTitle")
                        title = await title_el.inner_text() if title_el else ""
                        
                        link_el = await item.query_selector("a")
                        link = await link_el.get_attribute("href") if link_el else ""
                        if link and link.startswith("/"):
                            link = "https://www.zhihu.com" + link
                            
                        metrics_el = await item.query_selector(".HotItem-metrics, .HotList-itemMetrics")
                        metrics = await metrics_el.inner_text() if metrics_el else ""
                        
                        if title:
                            results.append({
                                "rank": rank.strip(),
                                "title": title.strip(),
                                "url": link,
                                "metrics": metrics.strip()
                            })
                    except Exception:
                        continue
                
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Failed to fetch hot list from {url}: {e}")
                continue
                
        raise Exception("无法从知乎获取热榜数据。可能触发了验证码或登录墙。")

    async def extract_content(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Extract main content from a Zhihu question or article."""
        if url:
            await self.page.goto(url)
        
        await self.page.wait_for_load_state("domcontentloaded")
        
        title_el = await self.page.query_selector(".QuestionHeader-title, .Post-Title")
        title = await title_el.inner_text() if title_el else await self.page.title()
        
        # Extract the main answer or article body
        content_el = await self.page.query_selector(".RichText, .Post-RichText")
        content = await content_el.inner_text() if content_el else "Could not extract content."
        
        return {
            "title": title,
            "content": content,
            "url": self.page.url
        }
