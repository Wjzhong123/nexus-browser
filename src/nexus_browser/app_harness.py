import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from playwright.async_api import BrowserContext, Page, async_playwright

logger = logging.getLogger("nexus_browser")


@dataclass
class RouteResult:
    """Simple result type for browser routing operations."""
    output: str = ""
    is_error: bool = False
    metadata: dict = field(default_factory=dict)


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
            if not element:
                return
            box = await element.bounding_box()
            if not box:
                return
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
            try:
                info.append({
                    "index": i,
                    "title": await page.title(),
                    "url": page.url,
                })
            except Exception:
                pass
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
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        # Resolve OpenCLI path: project root / opencli
        project_root = Path(__file__).resolve().parents[3]
        opencli_dir = project_root / "opencli"

        # Build command-line arguments
        full_args = ["bun", "src/main.ts", command, subcommand, *args, "--format", "json"]
        for k, v in kwargs.items():
            if v is True:
                full_args.append(f"--{k}")
            elif v is not False and v is not None:
                full_args.extend([f"--{k}", str(v)])

        env = os.environ.copy()
        env["OPENCLI_BROWSER_URL"] = "http://127.0.0.1:9222"
        env["OPENCLI_USER_DATA_DIR"] = str(Path.home() / ".one" / "browser_data")

        try:
            logger.info(f"Nexus running OpenCLI: {' '.join(full_args)}")
            process = await asyncio.create_subprocess_exec(
                *full_args, cwd=str(opencli_dir),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return {"status": "error", "message": stderr.decode().strip()}

            output = stdout.decode().strip()
            try:
                start = output.find("[") if "[" in output else output.find("{")
                if start != -1:
                    return {"status": "success", "result": json.loads(output[start:])}
                return {"status": "success", "result": output}
            except Exception:
                return {"status": "success", "result": output}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _find_cached_chromium() -> Optional[str]:
        """Find a usable Chrome for Testing in Playwright's cache directory.

        Prefers the latest available version. Returns None when no cache is found,
        letting Playwright download/error normally.
        This fixes chromium-1228 download stalls when local 1223/1208 already exist.
        """
        cache_root = Path.home() / "Library" / "Caches" / "ms-playwright"
        if not cache_root.exists():
            return None
        # Collect all chrome-mac* directories under chromium-* revisions
        candidates: list[Path] = []
        for rev_dir in cache_root.glob("chromium-*"):
            for app in rev_dir.glob(
                "chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
            ):
                candidates.append(app)
        if not candidates:
            return None
        # Sort by revision number descending (chromium-1223 > chromium-1208)
        def sort_key(p: Path) -> int:
            try:
                return int(p.parent.parent.parent.parent.name.split("-")[1])
            except (IndexError, ValueError):
                return 0
        candidates.sort(key=sort_key, reverse=True)
        return str(candidates[0])

    async def launch_standalone(self, user_data_dir: Optional[Path] = None) -> dict:
        """Launch a standalone persistent Chromium instance.

        Uses the locally cached Chrome for Testing when available, avoiding
        Playwright's chromium-1228 download stall.
        """
        await self.start()
        data_dir = user_data_dir or (Path.home() / ".nexus" / "browser_data")
        data_dir.mkdir(parents=True, exist_ok=True)

        launch_kwargs: dict[str, Any] = dict(
            user_data_dir=str(data_dir),
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-infobars",
                "--disable-background-networking",
            ],
        )
        # Prefer local cached browser to avoid Playwright re-download
        cached = self._find_cached_chromium()
        if cached:
            logger.info("Using locally cached browser: %s", cached)
            launch_kwargs["executable_path"] = cached

        try:
            self.context = await asyncio.wait_for(
                self.playwright.chromium.launch_persistent_context(**launch_kwargs),
                timeout=30.0,
            )
            if self.context.pages:
                self.current_page = self.context.pages[0]
            else:
                self.current_page = await asyncio.wait_for(
                    self.context.new_page(),
                    timeout=10.0,
                )
            self.pages = self.context.pages
            logger.info("Standalone browser instance started (data: %s)", data_dir)
            return {"status": "success", "message": "Standalone browser launched"}
        except Exception as e:
            logger.exception("Standalone browser launch failed")
            return {"status": "error", "message": str(e)}

    async def navigate_and_get(self, url: str) -> RouteResult:
        """Navigate to a URL and return page content as text.

        Creates a new page if none is active, and closes it after extraction
        to avoid orphan tab accumulation.
        """
        try:
            await self.start()
            if not self.context:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(Path.home() / ".nexus" / "browser_data"),
                    headless=False,
                )
                self.pages = self.context.pages

            page = await self.context.new_page()
            page.set_default_timeout(15000)
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=5000)
            title = await page.title()
            content = await page.inner_text("body")
            content = content[:8000] if len(content) > 8000 else content  # truncate
            await page.close()
            return RouteResult(
                output=f"## {title}\n\n{content}",
                is_error=False,
                metadata={"url": url, "title": title},
            )
        except Exception as e:
            try:
                await page.close()
            except Exception:
                pass
            return RouteResult(
                output=f"Failed to navigate to {url}: {e}",
                is_error=True,
                metadata={"url": url, "error": str(e)},
            )

    async def close_page(self, page: Optional[Page] = None):
        """Close a specific page or the current page.

        Prevents orphan tab accumulation from repeated browser operations.
        """
        target = page or self.current_page
        if target:
            try:
                await target.close()
            except Exception:
                pass

    async def close(self):
        """Close all browser resources."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
        self.browser = None
        self.playwright = None
        self.context = None
        self.current_page = None
        self.pages = []