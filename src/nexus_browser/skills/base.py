import httpx
import logging
from typing import Any, Dict, List, Optional
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger("nexus_browser.skills")

class BaseSkill:
    """Base class for all site-specific adapters (Skills)."""
    
    def __init__(self, harness: Any):
        self.harness = harness
        self.client = httpx.AsyncClient(timeout=10.0)

    @property
    def page(self) -> Page:
        return self.harness.current_page

    async def fetch_api(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Utility to fetch data from a JSON API."""
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"API Fetch error for {url}: {e}")
            return {"error": str(e)}

    async def get_parent_by_selector(self, element: ElementHandle, selector: str) -> Optional[ElementHandle]:
        """Climb up the DOM tree from an element to find a parent matching the selector."""
        try:
            # We use evaluate to find the parent in the browser context
            return await element.evaluate_handle(
                f"(el, sel) => el.closest(sel)", selector
            )
        except Exception:
            return None

    async def close(self):
        await self.client.aclose()
