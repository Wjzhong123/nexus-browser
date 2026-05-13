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

    async def _apply_stealth(self, page):
        """Apply stealth patches to the page to avoid bot detection."""
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
            logger.info("Stealth patches applied to page.")
        except ImportError:
            logger.warning("playwright-stealth not installed. Skipping stealth.")

    async def human_move(self, page, selector: str):
        """Simulate human-like mouse movement to a selector."""
        try:
            element = await page.query_selector(selector)
            if not element: return
            box = await element.bounding_box()
            if not box: return
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            await page.mouse.move(x, y, steps=10)
        except Exception as e:
            logger.error(f"Human move failed: {e}")

    async def attach(self, host: str = "127.0.0.1", port: int = 9222):
        """Connect to a running browser or Electron app via CDP."""
        await self.start()
        endpoint_url = f"http://{host}:{port}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{endpoint_url}/json/version")
                data = resp.json()
                ws_url = data.get("webSocketDebuggerUrl")
            if not ws_url:
                raise Exception(f"Could not find webSocketDebuggerUrl at {endpoint_url}")
            logger.info(f"Connecting to CDP at {ws_url}...")
            self.browser = await self.playwright.chromium.connect_over_cdp(ws_url)
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

    async def run_opencli(self, command: str, subcommand: str, args: List[str] = None, kwargs: Dict[str, Any] = None):
        """Execute an OpenCLI command through this harness."""
        if args is None: args = []
        if kwargs is None: kwargs = {}
        
        # Resolve OpenCLI path (assuming it's a peer package)
        # packages/nexus-browser/src/nexus_browser/app_harness.py -> packages/opencli
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        opencli_dir = os.path.join(base_dir, "opencli")
        
        full_args = ["bun", "src/main.ts", command, subcommand] + args
        for k, v in kwargs.items():
            if v is True: full_args.append(f"--{k}")
            elif v is not False and v is not None: full_args.extend([f"--{k}", str(v)])
        
        full_args += ["--format", "json"]
        
        env = os.environ.copy()
        env["OPENCLI_BROWSER_URL"] = f"http://127.0.0.1:9222"
        env["OPENCLI_USER_DATA_DIR"] = os.path.join(os.path.expanduser("~"), ".one", "browser_data")
        
        try:
            logger.info(f"Nexus running OpenCLI: {' '.join(full_args)}")
            process = await asyncio.create_subprocess_exec(
                *full_args, cwd=opencli_dir,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return {"status": "error", "message": stderr.decode().strip()}
            
            output = stdout.decode().strip()
            # Try parsing JSON
            import json
            try:
                start = output.find("[") if "[" in output else output.find("{")
                if start != -1: return {"status": "success", "result": json.loads(output[start:])}
                return {"status": "success", "result": output}
            except:
                return {"status": "success", "result": output}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.playwright = None
        self.context = None
        self.current_page = None
