// pages/index/index.js
const api = require('../../utils/api.js')

Page({
  data: {
    masterUrl: 'https://www.pku.edu.cn/department.html',
    statusMessage: '',
    statusClass: '',
    isRunning: false,
    jobPoller: null,
    // 教师列表相关
    teachers: [],
    totalCount: 0,
    isLoading: false,
    isLoadingMore: false,
    hasMore: true,
    currentPage: 0,
    pageSize: 20  // 每页显示20条
  },

  onLoad() {
    // 页面加载时检查任务状态
    this.checkJobStatus()
    // 加载教师列表
    this.loadTeachers()
  },

  onShow() {
    // 页面显示时刷新数据（从搜索页返回时）
    this.loadTeachers()
  },

  onUnload() {
    // 页面卸载时清除轮询
    if (this.data.jobPoller) {
      clearInterval(this.data.jobPoller)
    }
  },

  onMasterUrlInput(e) {
    this.setData({
      masterUrl: e.detail.value
    })
  },

  // 启动全流程自动化
  async startFullAutomation() {
    const { masterUrl } = this.data
    
    if (!masterUrl) {
      wx.showToast({
        title: '请输入大学院系主页网址！',
        icon: 'none'
      })
      return
    }

    wx.showModal({
      title: '确认启动',
      content: '确定要启动全流程自动化吗？\n这将是一个非常缓慢 (10-20分钟) 的后台任务。',
      success: async (res) => {
        if (res.confirm) {
          this.setData({
            statusMessage: '请求已发送！任务已在后台启动。正在获取实时状态...',
            statusClass: 'status-running',
            isRunning: true
          })

          try {
            const result = await api.startFullAutomation(masterUrl)
            
            if (result.status === 'success') {
              // 启动成功，开始轮询状态
              this.startPolling()
            } else {
              this.setData({
                statusMessage: `启动失败: ${result.message}`,
                statusClass: 'status-error',
                isRunning: false
              })
            }
          } catch (error) {
            this.setData({
              statusMessage: `请求失败: ${error.message}`,
              statusClass: 'status-error',
              isRunning: false
            })
            wx.showToast({
              title: '启动失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },

  // 检查任务状态
  async checkJobStatus() {
    try {
      const result = await api.checkStatus()
      
      this.setData({
        statusMessage: result.message
      })

      if (result.status === 'running') {
        this.setData({
          statusClass: 'status-running',
          isRunning: true
        })
        // 如果任务正在运行，开始轮询
        if (!this.data.jobPoller) {
          this.startPolling()
        }
      } else if (result.status === 'finished') {
        this.setData({
          statusClass: 'status-finished',
          isRunning: false
        })
        this.stopPolling()
        wx.showModal({
          title: '任务完成',
          content: '全流程自动化已完成！数据已自动刷新。',
          showCancel: false,
          success: () => {
            // 任务完成后自动刷新教师列表
            this.loadTeachers(true)
          }
        })
      } else if (result.status === 'error') {
        this.setData({
          statusClass: 'status-error',
          isRunning: false
        })
        this.stopPolling()
      } else {
        // idle状态
        this.setData({
          statusClass: '',
          isRunning: false
        })
      }
    } catch (error) {
      console.error('检查状态失败:', error)
    }
  },

  // 开始轮询
  startPolling() {
    if (this.data.jobPoller) {
      clearInterval(this.data.jobPoller)
    }
    
    const poller = setInterval(() => {
      this.checkJobStatus()
    }, 3000) // 每3秒检查一次

    this.setData({
      jobPoller: poller
    })
  },

  // 停止轮询
  stopPolling() {
    if (this.data.jobPoller) {
      clearInterval(this.data.jobPoller)
      this.setData({
        jobPoller: null
      })
    }
  },

  // 加载教师列表
  async loadTeachers(reset = true) {
    if (this.data.isLoading) return

    this.setData({
      isLoading: true
    })

    try {
      // 获取所有教师数据（不设置搜索条件）
      const result = await api.searchTeachers({})

      if (result.status === 'success') {
        const teachers = result.data || []
        const totalCount = teachers.length

        this.setData({
          teachers: reset ? teachers.slice(0, this.data.pageSize) : [...this.data.teachers, ...teachers.slice(this.data.currentPage * this.data.pageSize, (this.data.currentPage + 1) * this.data.pageSize)],
          totalCount: totalCount,
          hasMore: reset ? teachers.length > this.data.pageSize : (this.data.currentPage + 1) * this.data.pageSize < teachers.length,
          currentPage: reset ? 0 : this.data.currentPage + 1
        })
      } else {
        wx.showToast({
          title: result.message || '加载失败',
          icon: 'none'
        })
      }
    } catch (error) {
      console.error('加载教师列表失败:', error)
      wx.showToast({
        title: '加载失败: ' + error.message,
        icon: 'none'
      })
    } finally {
      this.setData({
        isLoading: false
      })
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
  },

  // 加载更多
  async loadMoreTeachers() {
    if (this.data.isLoadingMore || !this.data.hasMore) return

    this.setData({
      isLoadingMore: true
    })

    try {
      const result = await api.searchTeachers({})

      if (result.status === 'success') {
        const allTeachers = result.data || []
        const currentPage = this.data.currentPage + 1
        const startIndex = currentPage * this.data.pageSize
        const endIndex = startIndex + this.data.pageSize
        const newTeachers = allTeachers.slice(startIndex, endIndex)

        if (newTeachers.length > 0) {
          this.setData({
            teachers: [...this.data.teachers, ...newTeachers],
            currentPage: currentPage,
            hasMore: endIndex < allTeachers.length
          })
        } else {
          this.setData({
            hasMore: false
          })
        }
      }
    } catch (error) {
      console.error('加载更多失败:', error)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    } finally {
      this.setData({
        isLoadingMore: false
      })
    }
  }
})

