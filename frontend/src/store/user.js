import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUserInfo = (info) => {
    userInfo.value = info
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const fetchUserInfo = async () => {
    try {
      const res = await api.get('/auth/user-info')
      if (res.code === 200) {
        userInfo.value = res.data
      }
    } catch (error) {
      console.error('获取用户信息失败', error)
    }
  }

  return {
    userInfo,
    token,
    setToken,
    setUserInfo,
    logout,
    fetchUserInfo
  }
})
