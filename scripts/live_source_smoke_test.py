from modules.studio.playwright_video_collector import PlaywrightVideoCollector

collector = PlaywrightVideoCollector(headless=False, timeout_ms=15000)
print("상태:", collector.status())
rows = [
    {"platform": "douyin", "keyword": "厨房 收纳 视频", "search_url": "https://www.douyin.com/search/%E5%8E%A8%E6%88%BF%20%E6%94%B6%E7%BA%B3%20%E8%A7%86%E9%A2%91"},
    {"platform": "taobao", "keyword": "厨房 收纳 主图视频", "search_url": "https://s.taobao.com/search?q=%E5%8E%A8%E6%88%BF%20%E6%94%B6%E7%BA%B3%20%E4%B8%BB%E5%9B%BE%E8%A7%86%E9%A2%91"},
]
print(collector.collect(rows, limit_per_platform=3))
