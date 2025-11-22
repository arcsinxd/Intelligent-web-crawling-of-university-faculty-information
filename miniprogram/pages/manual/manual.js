// pages/manual/manual.js
const api = require('../../utils/api.js')

Page({
  data: {
    collegeName: '',
    facultyUrl: '',
    statusMessage: '',
    statusClass: '',
    isGenerating: false,
    recipeResult: ''
  },

  onCollegeNameInput(e) {
    this.setData({
      collegeName: e.detail.value
    })
  },

  onFacultyUrlInput(e) {
    this.setData({
      facultyUrl: e.detail.value
    })
  },

  async generateRecipe() {
    const { collegeName, facultyUrl } = this.data

    if (!collegeName || !facultyUrl) {
      wx.showToast({
        title: '学院名称和网址都不能为空！',
        icon: 'none'
      })
      return
    }

    this.setData({
      isGenerating: true,
      statusMessage: '正在下载 HTML 并请求 AI 分析...',
      statusClass: 'status-running',
      recipeResult: ''
    })

    try {
      const result = await api.generateRecipe(collegeName, facultyUrl)

      if (result.status === 'success') {
        this.setData({
          statusMessage: result.message,
          statusClass: 'status-finished',
          recipeResult: JSON.stringify(result.recipe, null, 2)
        })
        wx.showToast({
          title: '配方生成成功！',
          icon: 'success'
        })
      } else {
        this.setData({
          statusMessage: `生成失败: ${result.message}`,
          statusClass: 'status-error'
        })
        wx.showToast({
          title: '生成失败',
          icon: 'none'
        })
      }
    } catch (error) {
      this.setData({
        statusMessage: `请求失败: ${error.message}`,
        statusClass: 'status-error'
      })
      wx.showToast({
        title: '请求失败',
        icon: 'none'
      })
    } finally {
      this.setData({
        isGenerating: false
      })
    }
  }
})

