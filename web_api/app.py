# web_api/app.py

import os
import sys
import httpx 
import json
import time
from threading import Thread
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS  # 添加CORS支持，用于微信小程序跨域访问
from pymongo import MongoClient
from openai import OpenAI # <--- 1. 使用 OpenAI 库
from bs4 import BeautifulSoup

# ----------------------------------------------------
# !! 关键 !! 修正 Python 导入路径
# ----------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

try:
    from scrapy.crawler import CrawlerProcess
    
    # !! 关键修复 !!
    # 我们不再导入 'settings' 了，只导入爬虫本身
    from university_scraper.university_scraper.spiders.pku_generic_spider import PkuGenericSpider
    
except ImportError as e:
    print(f"严重错误: 无法导入 Scrapy 模块。请确保 'university_scraper' 文件夹存在。\n{e}")
    sys.exit(1)
# ----------------------------------------------------


# --- Flask 应用初始化 ---
app = Flask(__name__)
# 添加CORS支持，允许微信小程序跨域访问
CORS(app, resources={r"/api/*": {"origins": "*"}})  # 允许所有来源访问API（生产环境建议限制特定域名）
JOB_STATUS = {"status": "idle", "message": "系统就绪。"}

# --- 数据库连接 ---
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client.teacher_db
    recipe_collection = db.spider_recipes    
    teacher_collection = db.pku_cs_teachers  
    client.server_info()
    print("MongoDB 连接成功！")
except Exception as e:
    print(f"警告：无法连接到 MongoDB。\n错误: {e}")

# --- DeepSeek AI 客户端初始化 (使用 OpenAI 库) ---
try:
    # !! 替换成你的 DeepSeek Key !!
    DEEPSEEK_API_KEY = "sk-396fae50c55148f7a35875d11ba00f61" 
    if "YOUR_DEEPSEEK_API_KEY_HERE" in DEEPSEEK_API_KEY:
        print("警告: 请在 app.py 中填入你的 DEEPSEEK_API_KEY")
    
    ai_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com" # <--- 指向 DeepSeek
    )
except Exception as e:
    print(f"初始化 DeepSeek AI 客户端失败: {e}")
    ai_client = None

# ----------------------------------------------------
# 页面路由
# ----------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ----------------------------------------------------
# API 路由
# ----------------------------------------------------
@app.route('/api/start-full-automation', methods=['POST'])
def start_full_automation():
    global JOB_STATUS
    if JOB_STATUS.get("status") == "running":
        return jsonify({'status': 'error', 'message': '一个任务已经在运行中！请等待它完成。'}), 400
    data = request.json
    master_url = data.get('master_url')
    if not master_url:
        return jsonify({'status': 'error', 'message': '未提供大学院系主页 URL'}), 400
    JOB_STATUS = {"status": "running", "message": "任务已启动..."}
    app_context = app.app_context()
    thread = Thread(target=run_full_automation, args=(app_context, master_url))
    thread.daemon = True 
    thread.start()
    return jsonify({'status': 'success', 'message': '全流程自动化已在后台启动！'})

@app.route('/api/check-status', methods=['GET'])
def check_status():
    global JOB_STATUS
    return jsonify(JOB_STATUS)

@app.route('/api/search', methods=['GET'])
def search_teachers():
    # (此函数和之前一样，无需改动)
    try:
        query_name = request.args.get('name')
        query_college = request.args.get('college')
        query_research = request.args.get('research')
        mongo_filter = {}
        if query_name:
            mongo_filter['name'] = {'$regex': query_name, '$options': 'i'}
        if query_college:
            mongo_filter['department'] = {'$regex': query_college, '$options': 'i'}
        if query_research:
            mongo_filter['research_interests'] = {'$regex': query_research, '$options': 'i'}
        teachers_cursor = teacher_collection.find(mongo_filter, {'_id': 0}).limit(100)
        teachers_list = list(teachers_cursor)
        return jsonify({'status': 'success', 'data': teachers_list})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ----------------------------------------------------
# 全流程自动化的“真正”执行函数
# ----------------------------------------------------
# ----------------------------------------------------
# 全流程自动化的“真正”执行函数 (!! 完整版 !!)
# ----------------------------------------------------
def run_full_automation(app_context, master_url):
    global JOB_STATUS
    with app_context:
        try:
            print("\n" + "="*50)
            print("🤖 [全流程自动化任务已启动]")
            print("="*50 + "\n")
            
            # ----------------------------------------------------
            # [步骤 1: AI 1 爬取所有院系列表]
            # ----------------------------------------------------
            JOB_STATUS = {"status": "running", "message": f"步骤 1: 正在从 {master_url} 寻找院系列表..."}
            print(JOB_STATUS["message"])
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'}
            with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as http_client:
                response = http_client.get(master_url)
                soup = BeautifulSoup(response.text, 'html.parser')
            links_text = ""
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                if text and len(text) < 50:
                    links_text += f"<a href=\"{a['href']}\">{text}</a>\n"
            
            prompt_ai_1 = f"""
            你是一个网站导航分析机器人。下面是一个大学官网的“院系设置”页面的所有链接。
            请分析这些链接，找出所有【学术院系】（例如：数学科学学院、物理学院、信息科学技术学院），并忽略“图书馆”、“后勤部”、“规章制度”等非学术部门。

            链接列表 (只截取前15000字符):
            {links_text[:15000]}

            请严格按照 JSON 格式返回一个包含所有学术院系的列表：
            {{
              "departments": [
                {{ "name": "数学科学学院", "url": "..." }},
                {{ "name": "物理学院", "url": "..." }}
              ]
            }}
            """
            
            print("  步骤 1.1: 正在请求 AI 1 分析院系列表...")
            completion = ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt_ai_1}],
                response_format={"type": "json_object"}
            )
            response_data = json.loads(completion.choices[0].message.content)
            college_list_raw = response_data.get('departments', [])
            if not college_list_raw:
                raise Exception("AI 1 未能从主页上找到院系列表")

            college_list = []
            for college in college_list_raw:
                name = college.get('name')
                url_relative = college.get('url')
                if name and url_relative:
                    absolute_url = httpx.URL(master_url).join(url_relative)
                    college_list.append({'name': name, 'homepage_url': str(absolute_url)})
            
            JOB_STATUS = {"status": "running", "message": f"步骤 1 成功：AI 1 找到 {len(college_list)} 个院系。"}
            print(JOB_STATUS["message"])

            # ----------------------------------------------------
            # [步骤 2 & 3: AI 2/3 循环生成配方]
            # ----------------------------------------------------
            total = len(college_list)
            for i, college in enumerate(college_list):
                JOB_STATUS = {"status": "running", "message": f"步骤 2/3 ({i+1}/{total}): 正在为 {college['name']} 生成配方..."}
                print(f"\n{JOB_STATUS['message']}")
                try:
                    # --- 步骤 2: AI 2 找师资页 ---
                    print(f"  步骤 2: 正在下载 {college['name']} 的主页并寻找“师资”链接...")
                    with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as http_client:
                        response = http_client.get(college['homepage_url'])
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links_text = ""
                    for a in soup.find_all('a', href=True):
                        text = a.get_text(strip=True)
                        if text and len(text) < 30:
                            links_text += f"<a href=\"{a['href']}\">{text}</a>\n"

                    prompt_ai_2 = f"""
                    你是一个网址导航机器人。
                    下面是“{college['name']}”主页上的所有链接。
                    请从中找出一个【最可能】指向“师资队伍”、“教职工”、“学者教授”列表的链接（href）。
                    
                    链接列表:
                    {links_text[:10000]}

                    请严格按照 JSON 格式返回，只返回那个最相关的URL：
                    {{
                      "faculty_url": "..."
                    }}
                    """
                    completion = ai_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt_ai_2}],
                        response_format={"type": "json_object"}
                    )
                    faculty_url_relative = json.loads(completion.choices[0].message.content).get('faculty_url')
                    if not faculty_url_relative:
                        print(f"  > AI 2 未能找到“师资”链接。跳过 {college['name']}。")
                        continue
                    
                    faculty_url = str(httpx.URL(college['homepage_url']).join(faculty_url_relative))
                    print(f"  > AI 2 找到师资页: {faculty_url}")
                    
                    # --- 成本节约检查 ---
                    existing_recipe = recipe_collection.find_one({"start_url": faculty_url})
                    if existing_recipe:
                        print(f"  > 数据库中已存在此配方。跳过 AI 3。")
                        continue

                    # --- 步骤 3: AI 3 生成配方 ---
                    recipe = _generate_recipe_logic(faculty_url, college['name']) # 调用辅助函数
                    
                    # --- 步骤 3.5: 保存配方 ---
                    recipe_collection.update_one(
                        {'start_url': recipe['start_url']},
                        {'$set': recipe},
                        upsert=True
                    )
                    print(f"  > AI 3 成功: {college['name']} 的配方已保存到数据库！")
                    time.sleep(3) # 休息 3 秒
                except Exception as e_inner:
                    print(f"  > 处理 {college['name']} 时出错: {e_inner}")

            # ----------------------------------------------------
            # [步骤 4: 自动启动 Scrapy (硬编码)]
            # ----------------------------------------------------
            JOB_STATUS = {"status": "running", "message": f"步骤 4: 所有配方已生成！正在启动 Scrapy 爬虫抓取数据..."}
            print("\n" + "="*50)
            print(JOB_STATUS["message"])
            
            s = {
                # 1. 核心设置
                'BOT_NAME': 'university_scraper',
                'SPIDER_MODULES': ['university_scraper.university_scraper.spiders'],
                'NEWSPIDER_MODULE': 'university_scraper.university_scraper.spiders',
                
                # 2. 爬虫设置
                'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'ROBOTSTXT_OBEY': False,
                'DEFAULT_REQUEST_HEADERS': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                },
                
                # 3. Pipeline 和数据库
                'ITEM_PIPELINES': {
                   # !! 关键修复：必须使用双层嵌套路径 !!
                   'university_scraper.university_scraper.pipelines.MongoPipeline': 300,
                },
                'MONGO_URI': 'mongodb://localhost:27017/',
                'MONGO_DB': 'teacher_db',
                'MONGO_COLLECTION': 'pku_cs_teachers',
                
                # 4. API 密钥 (从本文件顶部的全局变量读取)
                'DEEPSEEK_API_KEY': DEEPSEEK_API_KEY, 
                
                # 5. Asyncio 和日志
                'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
                'LOG_LEVEL': 'INFO', 
            }
            
            process = CrawlerProcess(s)
            process.crawl(PkuGenericSpider)
            process.start() # <-- 这会阻塞，直到爬虫运行完毕
            
            JOB_STATUS = {"status": "finished", "message": f"全流程自动化任务已完成！已爬取所有学院。"}
            print("\n" + "="*50)
            print("🤖 [全流程自动化任务已完成]")
            print("="*50 + "\n")

        except Exception as e:
            print(f"!! [全流程自动化任务失败] !!: {e}")
            JOB_STATUS = {"status": "error", "message": f"任务失败: {e}"}

# ( ... _generate_recipe_logic 和 generate_recipe_manual ... )
# ( ... 这两个函数和之前一样，无需改动 ... )
def _generate_recipe_logic(url, college_name):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'}
        with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as http_client:
            response = http_client.get(url)
            response.raise_for_status() 
            html_content = response.text
    except Exception as e:
        print(f"    [AI配方] 下载 {url} 失败: {e}")
        raise
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'head', 'link']):
            tag.decompose()
        if soup.body:
            clean_html_tags = soup.body.prettify()
        else:
            clean_html_tags = soup.prettify()
        html_snippet = f"带标签的 HTML (用于找选择器): {clean_html_tags[:30000]}"
    except Exception as e:
        html_snippet = html_content[html_content.find('<body>'):html_content.find('</body>')][:30000]

    prompt = f"""
    你是一个专业的Web爬虫工程师。下面是一份被清洗过的大学师资页面的 HTML 源代码。
    你的任务是分析此HTML，并返回一个JSON对象，其中包含用于爬取它的关键CSS选择器。
    1. 找到包含了【每一位】教师信息的、可重复的HTML元素。这将作为 "list_selector"。
    2. 在这个 "list_selector" 元素【内部】，找到包含了所有相关文本（姓名、职称、简介等）的那个子元素。这将作为 "text_selector"。
    HTML源代码（已清洗）:
    ```html
    {html_snippet}
    ```
    请严格按照以下JSON格式返回，不要包含任何多余的解释：
    {{
      "list_selector": "...",
      "text_selector": "..."
    }}
    """
    try:
        print(f"    [AI配方] 正在请求 DeepSeek AI 分析(已清洗的) HTML...")
        completion = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        response_content = completion.choices[0].message.content
        ai_recipe = json.loads(response_content)
        list_selector = ai_recipe.get('list_selector')
        text_selector = ai_recipe.get('text_selector')
        if not list_selector or not text_selector:
            raise Exception("AI 未能返回有效的选择器")
        print(f"    [AI配方] AI 生成配方成功: {ai_recipe}")
    except Exception as e:
        print(f"    [AI配方] AI 配方生成失败: {e}")
        raise
    return {
        "college": college_name,
        "page_name": f"全自动生成 (v4)",
        "start_url": url,
        "list_selector": list_selector,
        "text_selector": text_selector
    }

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe_manual():
    if not ai_client:
        return jsonify({'status': 'error', 'message': 'AI 客户端未初始化'}), 500
    data = request.json
    url = data.get('url')
    college_name = data.get('college')
    if not url or not college_name:
        return jsonify({'status': 'error', 'message': '缺少 URL 或学院名称'}), 400
    try:
        recipe = _generate_recipe_logic(url, college_name)
        recipe_collection.update_one(
            {'start_url': recipe['start_url']},
            {'$set': recipe},
            upsert=True
        )
        return jsonify({'status': 'success', 'message': 'AI 配方已成功生成并保存！(v4)', 'recipe': recipe})
    except Exception as e:
        print(f"手动配方生成失败: {e}")
        return jsonify({'status': 'error', 'message': f'手动配G方生成失败: {e}'}), 500


# --- 启动服务器 ---
if __name__ == '__main__':
    # 监听所有网络接口(0.0.0.0)，允许从其他设备访问（包括微信小程序）
    # 如果只想本地访问，可以使用 host='127.0.0.1'
    print("\n" + "="*50)
    print("🚀 Flask 服务器启动中...")
    print("="*50)
    print(f"📡 本地访问: http://127.0.0.1:5000")
    print(f"📡 网络访问: http://你的IP地址:5000")
    print("="*50 + "\n")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)