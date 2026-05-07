import httpx
import asyncio

async def discover_apps(ports=[9222, 9223, 9444]):
    print(f"🔍 Searching for apps with remote debugging enabled on ports: {ports}...")
    for port in ports:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://127.0.0.1:{port}/json/version", timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"✅ Found App on Port {port}:")
                    print(f"   - Name: {data.get('Browser')}")
                    print(f"   - Protocol: {data.get('Protocol-Version')}")
                    print(f"   - WS URL: {data.get('webSocketDebuggerUrl')}")
        except Exception:
            # Port not open or no app found
            pass

if __name__ == "__main__":
    asyncio.run(discover_apps())
