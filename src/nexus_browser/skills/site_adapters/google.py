from typing import List, Dict
from nexus_browser.skills.base import BaseSkill

class GoogleSearchSkill(BaseSkill):
    """
    Robust Google Search Adapter.
    Uses 'parent-climbing' logic to accurately associate titles with snippets.
    """
    
    async def search(self, query: str) -> List[Dict[str, str]]:
        """Perform a Google search and return structured results."""
        url = f"https://www.google.com/search?q={query}"
        await self.page.goto(url)
        
        # Wait for results container
        await self.page.wait_for_selector("#rso")
        
        results = []
        
        # Find all search result headings
        headings = await self.page.query_selector_all("#rso h3")
        
        for heading in headings:
            try:
                # 1. Get Title
                title = await heading.inner_text()
                
                # 2. Find the link (should be a parent or close relative)
                link_el = await self.get_parent_by_selector(heading, "a")
                link = await link_el.get_attribute("href") if link_el else ""
                
                # 3. Find the snippet using 'parent-climbing'
                # Standard Google result containers often have data-hveid or class tF2Cxc
                container = await self.get_parent_by_selector(heading, "div.tF2Cxc, div[data-hveid]")
                snippet = ""
                if container:
                    # Look for the description text inside this specific container
                    snippet_el = await container.query_selector("div.VwiC3b, span.aCOpRe")
                    if snippet_el:
                        snippet = await snippet_el.inner_text()
                
                if title and link:
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })
            except Exception:
                continue
                
        return results
