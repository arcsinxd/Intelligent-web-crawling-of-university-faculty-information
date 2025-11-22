// utils/api.js - API请求封装
const app = getApp()

/**
 * 封装微信小程序的网络请求
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.apiBaseUrl + url,
      method: method,
      data: data,
      header: {
        'Content-Type': 'application/json'
      },
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

/**
 * API方法
 */
const api = {
  // 启动全流程自动化
  startFullAutomation(masterUrl) {
    return request('/api/start-full-automation', 'POST', { master_url: masterUrl })
  },

  // 检查任务状态
  checkStatus() {
    return request('/api/check-status', 'GET')
  },

  // 搜索教师
  searchTeachers(params) {
    return request('/api/search', 'GET', params)
  },

  // 手动生成配方
  generateRecipe(college, url) {
    return request('/api/generate-recipe', 'POST', { college, url })
  }
}

module.exports = api

