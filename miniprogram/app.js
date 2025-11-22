// app.js
App({
  onLaunch() {
    // 小程序启动时的初始化
    console.log('小程序启动')
  },
  globalData: {
    // ⚠️ 重要：小程序无法直接访问 localhost
    // 请使用本机IP地址，例如：http://10.67.68.22:5000
    // 获取本机IP方法：
    // Windows: ipconfig 查看 IPv4 地址
    // Mac/Linux: ifconfig 或 ip addr 查看 IP 地址
    
    // 本地开发（请替换为你的本机IP地址）
    // 根据你的网络配置，可能的IP地址：
    // - WLAN: 10.67.68.22
    // - 以太网: 192.168.56.1
    // 请选择实际连接到网络的接口IP
    apiBaseUrl: 'http://10.67.68.22:5000',  // ⚠️ 请修改为你的实际IP（通常是WLAN的IP）
    
    // 生产环境（部署到服务器后）
    // apiBaseUrl: 'https://your-domain.com'
    
    // 如果后端在本地运行，示例：
    // apiBaseUrl: 'http://192.168.1.100:5000'  // 替换为实际IP
  }
})

