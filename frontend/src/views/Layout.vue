<template>
  <el-container class="layout-container">
    <!-- 顶部导航 -->
    <el-header class="header">
      <div class="header-left">
        <h2 class="logo">
          <el-icon><DataLine /></el-icon>
          AI智能学习平台
        </h2>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ userStore.userInfo?.nickname || userStore.userInfo?.username }}
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="220px" class="aside">
        <el-menu
          :default-active="activeMenu"
          class="menu"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/analysis">
            <el-icon><TrendCharts /></el-icon>
            <span>AI学情分析</span>
          </el-menu-item>
          <el-menu-item index="/practice">
            <el-icon><EditPen /></el-icon>
            <span>智能刷题</span>
          </el-menu-item>
          <el-menu-item index="/wrong-question">
            <el-icon><Document /></el-icon>
            <span>错题本</span>
          </el-menu-item>
          <el-menu-item index="/profile">
            <el-icon><Setting /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

onMounted(() => {
  if (!userStore.userInfo) {
    userStore.fetchUserInfo()
  }
})

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
    }).catch(() => {})
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.header {
  background: linear-gradient(90deg, #409EFF 0%, #66b1ff 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left .logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-right .user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.aside {
  background-color: #304156;
  overflow-x: hidden;
}

.menu {
  border: none;
  height: 100%;
}

.main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
