# Scrapy settings for university_scraper project

# ----------------------------------------------------
# 1. 核心设置 (!! 解决 "Spider not found" 的关键 !!)
# ----------------------------------------------------
BOT_NAME = 'university_scraper'

# !! 关键 !!
# Scrapy 内部运行时，它认为自己是根
# 所以这里的路径是“单层”的
SPIDER_MODULES = ['university_scraper.spiders']
NEWSPIDER_MODULE = 'university_scraper.spiders'


# ----------------------------------------------------
# 2. 爬虫设置
# ----------------------------------------------------

# 伪装成浏览器
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

# 跳过 robots.txt
ROBOTSTXT_OBEY = False

# 添加一些基础的请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# ----------------------------------------------------
# 3. Pipeline 和数据库设置 (!! 你丢失的部分 !!)
# ----------------------------------------------------
# 激活我们的 Pipeline
ITEM_PIPELINES = {
   'university_scraper.pipelines.MongoPipeline': 300,
}

# MongoDB 数据库设置
MONGO_URI = 'mongodb://localhost:27017/'
MONGO_DB = 'teacher_db'
MONGO_COLLECTION = 'pku_cs_teachers' 


# ----------------------------------------------------
# 4. 你的 API 密钥 (!! 你丢失的部分 !!)
# ----------------------------------------------------
# !! 确保你把你的 DeepSeek 密钥粘贴在这里 !!
DEEPSEEK_API_KEY = 'sk-396fae50c55148f7a35875d11ba00f61'


# ----------------------------------------------------
# 5. 启用 Asyncio 反应器 (!! 你丢失的部分 !!)
# ----------------------------------------------------
# 这是让 "async def parse" 和 "process.start()" 能工作的关键
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"