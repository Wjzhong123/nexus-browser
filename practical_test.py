import httpx
import asyncio

async def run_practical_test():
    url = "http://127.0.0.1:8000"
    
    print("🚀 Starting Nexus Browser Practical Test...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Attach to Chrome
        print("🔗 Attaching to Chrome on 9222...")
        resp = await client.post(f"{url}/attach", json={"port": 9222})
        print(f"   Status: {resp.status_code}, Body: {resp.text}")
        
        # 2. Search Bilibili
        print("\n📺 Testing Bilibili Skill: Searching 'OpenHarness'...")
        resp = await client.post(f"{url}/execute", json={
            "skill_name": "search_bilibili",
            "args": ["OpenHarness"]
        })
        if resp.status_code == 200:
            results = resp.json().get("result", [])
            print(f"   ✅ Found {len(results)} videos.")
            for r in results[:3]:
                print(f"      - {r['title']} ({r['stats']})")
        else:
            print(f"   ❌ Bilibili search failed: {resp.text}")
            
        # 3. Search Zhihu
        print("\n💬 Testing Zhihu Skill: Searching 'AI Agent'...")
        resp = await client.post(f"{url}/execute", json={
            "skill_name": "search_zhihu",
            "args": ["AI Agent"]
        })
        if resp.status_code == 200:
            results = resp.json().get("result", [])
            print(f"   ✅ Found {len(results)} items.")
            for r in results[:3]:
                print(f"      - {r['title']}")
        else:
            print(f"   ❌ Zhihu search failed: {resp.text}")

if __name__ == "__main__":
    asyncio.run(run_practical_test())
