BOT_NAME = "pchome_scraper"

SPIDER_MODULES = ["pchome_scraper.spiders"]
NEWSPIDER_MODULE = "pchome_scraper.spiders"

ADDONS = {}

ITEM_PIPELINES = {
   "pchome_scraper.pipelines.MinioPipeline": 300,
}
# --- 偽裝設定 ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

ROBOTSTXT_OBEY = False

# 因為要開真的瀏覽器視窗，8 個視窗可能會讓電腦當機
# 先改成 2 或 4 比較安全
CONCURRENT_REQUESTS = 4 
CONCURRENT_REQUESTS_PER_DOMAIN = 2

RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY = 6 

RETRY_ENABLED = True
RETRY_TIMES = 3

TELNETCONSOLE_ENABLED = False
FEED_EXPORT_ENCODING = "utf-8"

# # 為了配合 Playwright，這裡必須指定為 Asyncio 核心
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# # 啟動 Playwright 下載器 (這是讓 Scrapy 呼叫 Chrome 的關鍵)
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }


# # Playwright 隱形與防偵測設定

# # 3. 瀏覽器啟動參數 (Launch Options)
# PLAYWRIGHT_LAUNCH_OPTIONS = {
#     "headless": False,  # 設為 False 親眼看到瀏覽器跳出來 (除錯用)
#     "args": [
#         # 這行是核心！關閉 "Chrome 正受到自動化軟體控制" 的特徵
#         "--disable-blink-features=AutomationControlled", 
#         "--no-sandbox",
#         "--disable-infobars",
#         "--start-maximized", # 視窗最大化
#     ]
# }

# # 4. 瀏覽器上下文設定 (Context Args)
# PLAYWRIGHT_CONTEXT_ARGS = {
#     # 強制設定為大螢幕解析度 (避免 PChome 變成手機版選單)
#     "viewport": {
#         "width": 1920,
#         "height": 1080,
#     },
#     # 確保 User-Agent 跟上面 Scrapy 的一致
#     "user_agent": USER_AGENT,
#     "java_script_enabled": True,
#     "ignore_https_errors": True,
# }

# # 顯示 Playwright 的 Log，方便除錯
# LOG_LEVEL = 'INFO'