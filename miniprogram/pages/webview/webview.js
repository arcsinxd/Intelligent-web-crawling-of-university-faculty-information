// pages/webview/webview.js
Page({
  data: {
    url: ''
  },

  onLoad(options) {
    // 从页面参数中获取URL
    const url = decodeURIComponent(options.url || '')
    
    if (!url) {
      wx.showToast({
        title: 'URL参数错误',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
      return
    }

    // 确保URL是完整的（包含协议）
    let finalUrl = url
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      finalUrl = 'https://' + url
    }

    this.setData({
      url: finalUrl
    })

    // 设置导航栏标题
    wx.setNavigationBarTitle({
      title: '个人主页'
    })
  }
})

