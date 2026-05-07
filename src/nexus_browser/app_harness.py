import asyncio
import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, BrowserContext, Page

logger = logging.getLogger("nexus_browser")

class AppHarness:
    """
    Nexus App Harness - Controls both Web Browsers and Electron Apps.
    Inspired by OpenCLI and OpenHarness.
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.pages: List[Page] = []
        self.current_page: Optional[Page] = None

    async def start(self):
        """Initialize playwright."""
        if not self.playwright:
            self.playwright = await async_playwright().start()

    async def attach(self, host: str = "127.0.0.1", port: int = 9222):
        """
        Connect to a running browser or Electron app via CDP.
        This is the core feature for controlling desktop apps.
        """
        await self.start()
        
        # We use connect_over_cdp to attach to an existing debug port
        endpoint_url = f"http://{host}:{port}"
        
        try:
            # First, check if the port is open and get the websocket debugger URL
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{endpoint_url}/json/version")
                data = resp.json()
                ws_url = data.get("webSocketDebuggerUrl")
                
            if not ws_url:
                raise Exception(f"Could not find webSocketDebuggerUrl at {endpoint_url}")

            logger.info(f"Connecting to CDP at {ws_url}...")
            self.browser = await self.playwright.chromium.connect_over_cdp(ws_url)
            
            # Electron apps often have multiple contexts or just one
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
                self.pages = self.context.pages
                if self.pages:
                    self.current_page = self.pages[0]
            
            logger.info(f"Successfully attached to app at port {port}")
            return {"status": "success", "app": data.get("Browser", "Unknown")}
            
        except Exception as e:
            logger.error(f"Failed to attach: {e}")
            return {"status": "error", "message": str(e)}

    async def get_pages_info(self) -> List[Dict[str, str]]:
        """Return info about all open tabs/windows in the attached app."""
        if not self.context:
            return []
        
        info = []
        for i, page in enumerate(self.context.pages):
            info.append({
                "index": i,
                "title": await page.title(),
                "url": page.url
            })
        return info

    async def switch_page(self, index: int):
        """Switch active control to a specific window/tab."""
        if self.context and 0 <= index < len(self.context.pages):
            self.current_page = self.context.pages[index]
            return True
        return False

    async def screenshot(self):
        """Capture screenshot of the current active window."""
        if not self.current_page:
            return None
        return await self.current_page.screenshot()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.playwright = None
        self.context = None
        self.current_page = None
