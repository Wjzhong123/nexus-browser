import asyncio
from typing import Dict, List, Optional

import httpx

__all__ = ["discover_apps", "main"]


async def discover_apps(ports: Optional[List[int]] = None) -> List[Dict[str, str]]:
    """Search for apps with remote debugging enabled on the given ports.

    Returns a list of dicts with keys: ``port``, ``name``, ``protocol``, ``ws_url``.
    """
    if ports is None:
        ports = [9222, 9223, 9444]

    results: List[Dict[str, str]] = []
    for port in ports:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"http://127.0.0.1:{port}/json/version", timeout=1.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results.append({
                        "port": str(port),
                        "name": data.get("Browser", "Unknown"),
                        "protocol": data.get("Protocol-Version", ""),
                        "ws_url": data.get("webSocketDebuggerUrl", ""),
                    })
        except Exception:
            pass
    return results


def main():
    """CLI entry point: print discovered apps in human-readable format."""
    found = asyncio.run(discover_apps())
    if not found:
        print("No apps with remote debugging found.")
        return
    print(f"🔍 Found {len(found)} app(s) with remote debugging enabled:")
    for app in found:
        print(f"  ✅ Port {app['port']}: {app['name']}")
        print(f"     WS: {app['ws_url']}")


if __name__ == "__main__":
    main()