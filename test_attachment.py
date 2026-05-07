import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from nexus_browser.app_harness import AppHarness

async def test_nexus():
    harness = AppHarness()
    print("🚀 Nexus Browser: Attempting to attach to Chrome on port 9222...")
    
    result = await harness.attach(port=9222)
    
    if result["status"] == "success":
        print(f"✅ Attached successfully to: {result['app']}")
        
        pages = await harness.get_pages_info()
        print(f"\n📂 Currently Open Tabs/Windows ({len(pages)}):")
        for p in pages:
            print(f"   [{p['index']}] {p['title'][:50]}... ({p['url'][:50]})")
            
        if harness.current_page:
            title = await harness.current_page.title()
            print(f"\n🎯 Active Target: {title}")
        
        await harness.close()
    else:
        print(f"❌ Failed to attach: {result['message']}")
        print("💡 Hint: Make sure Chrome is running with --remote-debugging-port=9222")

if __name__ == "__main__":
    asyncio.run(test_nexus())
