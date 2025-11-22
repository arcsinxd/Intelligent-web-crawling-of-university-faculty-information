// pages/search/search.js
const api = require('../../utils/api.js')

Page({
  data: {
    nameQuery: '',
    collegeQuery: '',
    researchQuery: '',
    teachers: [],
    hasSearched: false,
    isSearching: false
  },

  onNameInput(e) {
    this.setData({
      nameQuery: e.detail.value
    })
  },

  onCollegeInput(e) {
    this.setData({
      collegeQuery: e.detail.value
    })
  },

  onResearchInput(e) {
    this.setData({
      researchQuery: e.detail.value
    })
  },

  async searchTeachers() {
    const { nameQuery, collegeQuery, researchQuery } = this.data

    // 如果所有查询条件都为空，提示用户
    if (!nameQuery && !collegeQuery && !researchQuery) {
      wx.showToast({
        title: '请输入至少一个搜索条件',
        icon: 'none'
      })
      return
    }

    this.setData({
      isSearching: true,
      hasSearched: true
    })

    wx.showLoading({
      title: '搜索中...',
      mask: true
    })

    try {
      const params = {}
      if (nameQuery) params.name = nameQuery
      if (collegeQuery) params.college = collegeQuery
      if (researchQuery) params.research = researchQuery

      const result = await api.searchTeachers(params)

      if (result.status === 'success') {
        this.setData({
          teachers: result.data || []
        })
      } else {
        wx.showToast({
          title: result.message || '搜索失败',
          icon: 'none'
        })
        this.setData({
          teachers: []
        })
      }
    } catch (error) {
      wx.showToast({
        title: '请求失败: ' + error.message,
        icon: 'none'
      })
      this.setData({
        teachers: []
      })
    } finally {
      this.setData({
        isSearching: false
      })
      wx.hideLoading()
    }
  },

  // 打开个人主页
  openProfileUrl(e) {
    const url = e.currentTarget.dataset.url
    if (!url) {
      wx.showToast({
        title: 'URL无效',
        icon: 'none'
      })
      return
    }

    // 跳转到webview页面
    wx.navigateTo({
      url: `/pages/webview/webview?url=${encodeURIComponent(url)}`
    })
  }
})

