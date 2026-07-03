from typing import List, Dict, Any
import logging
from nexus_browser.skills.base import BaseSkill

logger = logging.getLogger("nexus_browser.skills.reddit")

class RedditSkill(BaseSkill):
    """
    Reddit Adapter for Search and Content extraction.
    """
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search subreddits and posts on Reddit."""
        url = f"https://www.reddit.com/search/?q={query}"
        logger.info(f"Searching Reddit for: {query}")
        
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for search results
        try:
            await self.page.wait_for_selector("faceplate-tracker, shreddit-post", timeout=10000)
        except Exception:
            logger.warning("Timeout waiting for Reddit search results")
            return []
            
        results = []
        # Reddit's new UI uses shreddit-post or similar custom elements
        items = await self.page.query_selector_all("shreddit-post, [data-testid='post-container']")
        for item in items[:10]:
            try:
                title_el = await item.query_selector("a[slot='title'], [data-adclicklocation='title']")
                title = await title_el.inner_text() if title_el else ""
                
                link_el = await item.query_selector("a[slot='full-post-link'], a[data-click-id='body']")
                link = await link_el.get_attribute("href") if link_el else ""
                if link and link.startswith("/"):
                    link = "https://www.reddit.com" + link
                
                author_el = await item.query_selector("[author], .author")
                author = await author_el.get_attribute("author") if author_el else "unknown"
                
                if title and link:
                    results.append({
                        "title": title.strip(),
                        "url": link,
                        "author": author,
                        "source": "Reddit"
                    })
            except Exception:
                continue
        return results

    async def get_subreddit_posts(self, subreddit: str, sort: str = "hot") -> List[Dict[str, Any]]:
        """Get top posts from a specific subreddit."""
        url = f"https://www.reddit.com/r/{subreddit}/{sort}/"
        logger.info(f"Fetching posts from r/{subreddit} sorted by {sort}")
        
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self.page.wait_for_selector("shreddit-post", timeout=10000)
        
        items = await self.page.query_selector_all("shreddit-post")
        results = []
        for item in items[:15]:
            try:
                title = await item.get_attribute("post-title") or ""
                link = await item.get_attribute("content-href") or ""
                score = await item.get_attribute("score") or "0"
                author = await item.get_attribute("author") or "unknown"
                
                if title:
                    results.append({
                        "title": title,
                        "url": link,
                        "score": score,
                        "author": author
                    })
            except Exception:
                continue
        return results

    async def extract_post(self, url: str) -> Dict[str, Any]:
        """Extract post content and top comments."""
        logger.info(f"Extracting content from Reddit post: {url}")
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for the post content
        await self.page.wait_for_selector("shreddit-post", timeout=10000)
        
        post_el = await self.page.query_selector("shreddit-post")
        title = await post_el.get_attribute("post-title") if post_el else "Unknown Title"
        
        # Extract selftext (if it's a text post)
        content_el = await self.page.query_selector("[slot='text-body'], .py-xs")
        content = await content_el.inner_text() if content_el else "[No text content/Media post]"
        
        # Extract top comments
        comments = []
        comment_elements = await self.page.query_selector_all("shreddit-comment")
        for cmd in comment_elements[:5]:
            try:
                author = await cmd.get_attribute("author") or "unknown"
                score = await cmd.get_attribute("score") or "0"
                body_el = await cmd.query_selector("[slot='comment']")
                body = await body_el.inner_text() if body_el else ""
                if body:
                    comments.append({
                        "author": author,
                        "score": score,
                        "text": body.strip()
                    })
            except Exception:
                continue
                
        return {
            "title": title,
            "content": content,
            "url": url,
            "top_comments": comments
        }
