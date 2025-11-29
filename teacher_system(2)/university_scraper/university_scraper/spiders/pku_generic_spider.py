# university_scraper/university_scraper/spiders/pku_generic_spider.py

import scrapy
import json
import asyncio
import pymongo
from openai import OpenAI  # <--- !! 1. 确保这里是 OpenAI !!
from ..items import TeacherItem # <--- !! 2. 确保这里是 '..' (相对导入) !!

class PkuGenericSpider(scrapy.Spider):
    name = 'pku_generic'
    
    def start_requests(self):
        """
        启动时，先加载配方，然后加载已处理的 URL 列表
        """
        self.logger.info("正在连接 MongoDB 读取爬虫配方...")
        
        mongo_uri = self.settings.get('MONGO_URI')
        mongo_db = self.settings.get('MONGO_DB')
        
        try:
            client = pymongo.MongoClient(mongo_uri)
            db = client[mongo_db]
            
            # 1. 加载配方
            self.recipes = list(db.spider_recipes.find())
            
            # 2. !! 成本节约逻辑 (AI 4) !!
            self.processed_urls = set()
            cursor = db.pku_cs_teachers.find({"name": {"$exists": True, "$ne": None}}, {"profile_url": 1})
            for doc in cursor:
                self.processed_urls.add(doc['profile_url'])
            self.logger.info(f"数据库中已有 {len(self.processed_urls)} 条已处理的教师数据，本次将跳过它们。")

            client.close()
            
            if not self.recipes:
                raise Exception("错误：在 'spider_recipes' 集合中没有找到任何配方！")
            self.logger.info(f"成功加载 {len(self.recipes)} 条爬虫配方。")
            
        except Exception as e:
            self.logger.error(f"加载配方或已处理 URL 失败: {e}")
            self.recipes = []

        if not self.recipes:
            self.logger.error("没有可用的配方，爬虫即将停止。")
            return

        for recipe in self.recipes:
            yield scrapy.Request(
                url=recipe['start_url'],
                callback=self.parse,
                cb_kwargs={
                    'college': recipe['college'],
                    'list_selector': recipe['list_selector'],
                    'text_selector': recipe['text_selector']
                }
            )

    async def parse(self, response, college, list_selector, text_selector):
        self.logger.info(f"成功访问: {response.url}")
        
        teacher_list_items = response.css(list_selector)
        
        if not teacher_list_items:
            self.logger.warning(f"在 {response.url} 上没有找到任何教师条目 (使用选择器: {list_selector})")
            return

        tasks = []
        new_teacher_count = 0
        for li in teacher_list_items:
            con_div = li.css(text_selector)
            if not con_div:
                continue 
            raw_text = ' '.join(con_div.css('*::text').getall())
            raw_text = ' '.join(raw_text.split()) 
            if not raw_text:
                continue 
            profile_url_relative = li.css('a::attr(href)').get()
            if not profile_url_relative:
                 profile_url_relative = response.url 
            item_url = response.urljoin(profile_url_relative)
            
            # !! 成本节约检查 (AI 4) !!
            if item_url in self.processed_urls:
                continue # 跳过这个教师，不调用 AI
            
            new_teacher_count += 1
            item = TeacherItem()
            item['profile_url'] = item_url
            item['university'] = '北京大学'
            item['department'] = college
            item['raw_text'] = raw_text
            tasks.append(asyncio.to_thread(self.process_with_ai, item, raw_text))

        self.logger.info(f"在 {response.url} 找到 {len(teacher_list_items)} 个条目，其中 {new_teacher_count} 个是新条目。")
        if not tasks:
            return # 没有新任务，提前退出

        self.logger.info(f"正在等待 {len(tasks)} 个 AI 任务 (来自 {college}) 完成...")
        results = await asyncio.gather(*tasks)
        self.logger.info(f"{college} 的 AI 任务已完成。")

        for item in results:
            if item:
                yield item

    # 3. (在线程中) 调用 DeepSeek AI
    def process_with_ai(self, item, raw_text):
        """
        这个函数在单独的线程中运行
        """
        
        # !! 确保这段代码的缩进在 'process_with_ai' 函数内部 !!
        try:
            api_key = self.settings.get('DEEPSEEK_API_KEY') 
            if not api_key:
                self.logger.error("未在 settings.py 中找到 DEEPSEEK_API_KEY")
                raise ValueError("未在 settings.py 中找到 DEEPSEEK_API_KEY")
            
            # !! 3. 确保这里是 OpenAI !!
            client = OpenAI( 
                api_key=api_key,
                base_url="https://api.deepseek.com" # <--- 指向 DeepSeek
            )
        except Exception as e:
            self.logger.error(f"初始化 DeepSeek AI 模型失败: {e}")
            return None 

        self.logger.info(f"正在使用 [DeepSeek AI] 智能处理: {item['profile_url']}")
        
        prompt = f"""
        你是一个数据提取机器人。请从以下教师简介文本中提取所需信息，并严格按照 JSON 格式返回。
        这段文本非常简洁，请精确提取。所需字段：
        - "name": 姓名
        - "title": 职称
        - "email": 电子邮件地址 (如果找不到则为 null)
        - "research_interests": 研究方向 (如果找不到则为 null)
        注意事项：
        1. 严格返回 JSON 格式，不要包含任何 JSON 之外的描述性文字。
        2. "name" 应该只包含姓名，不要包含 "职称：" 等前缀。
        --- 待提取的原始文本 ---
        {raw_text[:4000]}
        """
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} 
            )
            response_content = response.choices[0].message.content
            ai_data = json.loads(response_content)
            
            item['name'] = ai_data.get('name')
            item['title'] = ai_data.get('title')
            item['email'] = ai_data.get('email')
            item['research_interests'] = ai_data.get('research_interests')
            
            self.logger.info(f"DeepSeek AI 处理成功: {item['name']}")
            return item
            
        except Exception as e:
            self.logger.error(f"DeepSeek AI API 调用失败: {e}")
            return None