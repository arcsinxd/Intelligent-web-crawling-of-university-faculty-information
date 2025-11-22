import scrapy

class TeacherItem(scrapy.Item):
    name = scrapy.Field()           # 姓名
    title = scrapy.Field()          # 职称
    email = scrapy.Field()          # 邮箱
    profile_url = scrapy.Field()    # 个人主页链接
    university = scrapy.Field()     # 大学
    department = scrapy.Field()     # 院系
    research_interests = scrapy.Field() # 研究方向
    raw_text = scrapy.Field()       # 原始介绍文本 (用于 AI 提取)