# 高校教师信息系统 - 微信小程序

这是将网页端高校教师信息系统移植到微信小程序的版本。

## 项目结构

```
miniprogram/
├── app.js              # 小程序入口文件
├── app.json            # 小程序全局配置
├── app.wxss            # 小程序全局样式
├── sitemap.json        # 小程序站点地图配置
├── project.config.json # 小程序项目配置
├── pages/              # 页面目录
│   ├── index/          # 首页（全流程自动化）
│   ├── search/         # 搜索页
│   └── manual/         # 手动配方生成页
└── utils/              # 工具类
    └── api.js          # API请求封装
```

## 功能说明

### 1. 首页（index）
- 启动全流程自动化爬取任务
- 实时显示任务状态
- 快速导航到其他页面

### 2. 搜索页（search）
- 按姓名搜索教师
- 按学院搜索教师
- 按研究方向搜索教师
- 显示搜索结果列表

### 3. 手动生成页（manual）
- 手动输入学院名称和师资网址
- 使用AI生成爬虫配方
- 显示生成的配方结果

## 配置说明

### 1. 修改API地址

在 `app.js` 中修改 `apiBaseUrl`：

```javascript
globalData: {
  // 开发环境（本地）
  apiBaseUrl: 'http://localhost:5000',
  
  // 生产环境（部署到服务器后）
  // apiBaseUrl: 'https://your-domain.com'
}
```

### 2. 配置小程序AppID

在 `project.config.json` 中修改 `appid`：

```json
{
  "appid": "your-appid-here"
}
```

### 3. 后端CORS配置

确保后端Flask应用已安装并配置CORS支持：

```bash
pip install flask-cors
```

后端代码已添加CORS支持，允许小程序跨域访问。

## 使用步骤

1. **安装依赖**
   - 后端需要安装 `flask-cors`：`pip install flask-cors`

2. **启动后端服务**
   ```bash
   cd web_api
   python app.py
   ```

3. **配置小程序**
   - 在微信开发者工具中打开 `miniprogram` 目录
   - 修改 `app.js` 中的 `apiBaseUrl` 为实际后端地址
   - 修改 `project.config.json` 中的 `appid`

4. **开发调试**
   - 在微信开发者工具中点击"编译"
   - 如果后端在本地运行，需要在"设置"->"项目设置"->"本地设置"中勾选"不校验合法域名"

5. **部署上线**
   - 将后端部署到服务器（需要HTTPS）
   - 在小程序管理后台配置服务器域名
   - 修改 `app.js` 中的 `apiBaseUrl` 为服务器地址

## 注意事项

1. **域名配置**：小程序正式版必须使用已备案的HTTPS域名，需要在微信公众平台配置服务器域名白名单。

2. **本地开发**：开发时可以在微信开发者工具中关闭域名校验，但正式发布前必须配置正确的域名。

3. **网络请求**：小程序使用 `wx.request` 进行网络请求，已封装在 `utils/api.js` 中。

4. **页面导航**：使用 `navigator` 组件或 `wx.navigateTo` API 进行页面跳转。

5. **图标资源**：`app.json` 中配置了tabBar图标，需要准备以下图标文件：
   - `images/home.png` 和 `images/home-active.png`
   - `images/search.png` 和 `images/search-active.png`
   - `images/settings.png` 和 `images/settings-active.png`

## 与网页版的区别

1. **UI框架**：使用微信小程序的WXML/WXSS替代HTML/CSS
2. **网络请求**：使用 `wx.request` 替代 `fetch`
3. **页面跳转**：使用小程序导航API替代浏览器导航
4. **样式单位**：使用 `rpx`（响应式像素单位）替代 `px`
5. **组件系统**：使用小程序组件替代HTML元素

## 技术支持

如有问题，请检查：
1. 后端服务是否正常运行
2. API地址配置是否正确
3. 网络请求是否被拦截（域名白名单）
4. 小程序开发者工具的控制台错误信息

