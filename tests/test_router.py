"""Tests for the Nexus Browser web task router."""

from nexus_browser.router import resolve_site, resolve_intent, extract_query


# ── resolve_site ──

def test_resolve_site_by_url():
    """URL host should be resolved."""
    assert resolve_site("打开 https://www.zhihu.com/question/1") == "zhihu"


def test_resolve_site_by_url_not_in_list():
    """URL host not in OpenCLI list returns the host as-is."""
    assert resolve_site("打开 https://example.com/page") == "example"


def test_resolve_site_by_chinese_alias():
    assert resolve_site("看看知乎热搜") == "zhihu"
    assert resolve_site("B站有什么好视频") == "bilibili"
    assert resolve_site("哔哩哔哩热门") == "bilibili"
    assert resolve_site("小红书穿搭推荐") == "xiaohongshu"
    assert resolve_site("公众号文章搜索") == "weixin"


def test_resolve_site_by_english_name():
    assert resolve_site("github上的langchain项目") == "github"
    assert resolve_site("reddit热门帖子") == "reddit"


def test_resolve_site_none():
    assert resolve_site("今天天气怎么样") is None


def test_resolve_site_url_x_not_misparsed_as_twitter():
    """URL 'x' in example.com should NOT match twitter alias."""
    result = resolve_site("打开 https://example.com")
    assert result == "example", f"Got {result!r}, expected 'example'"


def test_resolve_site_mixed_case():
    assert resolve_site("B站热门") == "bilibili"
    assert resolve_site("GitHub搜索") == "github"


# ── resolve_intent ──

def test_resolve_intent_hot():
    assert resolve_intent("看看知乎热搜") == "hot"
    assert resolve_intent("今天的热门话题") == "hot"
    assert resolve_intent("bilibili trending") == "hot"


def test_resolve_intent_search():
    assert resolve_intent("搜一下B站上的AI视频") == "search"
    assert resolve_intent("在github上查找langchain") == "search"
    assert resolve_intent("找一下公众号文章") == "search"


def test_resolve_intent_detail():
    assert resolve_intent("看这个知乎回答的内容") == "detail"
    assert resolve_intent("打开这个页面") == "detail"


def test_resolve_intent_news():
    assert resolve_intent("最新新闻") == "news"
    assert resolve_intent("科技资讯") == "news"


def test_resolve_intent_default():
    assert resolve_intent("随便看看") == "detail"


# ── extract_query ──

def test_extract_query_explicit():
    """Explicit query should override auto-extraction."""
    result = extract_query("搜一下B站AI视频", "search", explicit_query="deep learning")
    assert result == "deep learning"


def test_extract_query_not_search():
    """Non-search intent should return None."""
    assert extract_query("看看知乎热搜", "hot") is None
    assert extract_query("今天天气", "detail") is None


def test_extract_query_auto_search():
    """Auto-extract query from search tasks."""
    result = extract_query("搜一下B站上的AI视频", "search")
    assert result is not None
    assert "AI视频" in result or "AI" in result


def test_extract_query_weixin_article():
    """Search for WeChat articles."""
    result = extract_query("搜索公众号文章，主题是AI创业", "search")
    assert result is not None
    assert "AI创业" in result or "AI" in result


def test_extract_query_github():
    """Search on GitHub."""
    result = extract_query("在github上查找langchain", "search")
    assert result is not None
    assert "langchain" in result


def test_extract_query_site_names_cleaned():
    """Site names should be removed from extracted query."""
    result = extract_query("搜一下B站上的AI视频", "search")
    if result:
        # "B站" should not appear in the final query
        assert "B站" not in result


def test_extract_query_empty():
    """Empty query should return None."""
    result = extract_query("搜一下", "search")
    assert result is None or result == ""


# ── Full routing scenarios ──

def test_router_scenario_zhihu_hot():
    """'看看知乎热搜' → zhihu + hot"""
    assert resolve_site("看看知乎热搜") == "zhihu"
    assert resolve_intent("看看知乎热搜") == "hot"


def test_router_scenario_bilibili_search():
    """'搜一下B站上的AI视频' → bilibili + search + query"""
    assert resolve_site("搜一下B站上的AI视频") == "bilibili"
    assert resolve_intent("搜一下B站上的AI视频") == "search"


def test_router_scenario_weixin_article():
    """'搜索公众号文章，主题是AI创业' → weixin + search + query"""
    assert resolve_site("搜索公众号文章，主题是AI创业") == "weixin"
    assert resolve_intent("搜索公众号文章，主题是AI创业") == "search"


def test_router_scenario_github_search():
    """'在github上找langchain' → github + search + query"""
    assert resolve_site("在github上找langchain") == "github"
    assert resolve_intent("在github上找langchain") == "search"


def test_router_scenario_xiaohongshu_trending():
    """'小红书穿搭推荐' → xiaohongshu + detail (推荐 not in hot keywords)"""
    assert resolve_site("小红书穿搭推荐") == "xiaohongshu"
    # "推荐" triggers detail, not search (it's a recommendation discovery)
    assert resolve_intent("小红书穿搭推荐") == "detail"


def test_router_scenario_url_open():
    """'打开 https://example.com/page' → URL host resolved"""
    assert resolve_site("打开 https://example.com/page") == "example"


def test_router_scenario_reddit_search():
    """'搜索reddit上的python内容' → reddit + search + query"""
    assert resolve_site("搜索reddit上的python内容") == "reddit"
    assert resolve_intent("搜索reddit上的python内容") == "search"


def test_router_scenario_news_search():
    """'最新科技新闻' → news intent"""
    assert resolve_intent("最新科技新闻") == "news"


def test_router_scenario_douyin_trending():
    """'抖音热门' → douyin + hot"""
    assert resolve_site("抖音热门") == "douyin"
    assert resolve_intent("抖音热门") == "hot"