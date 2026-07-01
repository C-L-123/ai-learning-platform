<template>
  <div class="profile">
    <h2 class="page-title">个人中心</h2>

    <el-row :gutter="20">
      <!-- 用户信息卡片 -->
      <el-col :span="8">
        <el-card class="user-card">
          <div class="user-avatar">
            <el-avatar :size="100" :icon="UserFilled" />
          </div>
          <div class="user-info">
            <h3>{{ userStore.userInfo?.nickname || userStore.userInfo?.username }}</h3>
            <p>用户名：{{ userStore.userInfo?.username }}</p>
            <p>邮箱：{{ userStore.userInfo?.email }}</p>
            <p>注册时间：{{ userStore.userInfo?.created_at }}</p>
          </div>
        </el-card>

        <!-- 学习数据概览 -->
        <el-card class="data-card" style="margin-top: 20px">
          <template #header>
            <span class="card-title">学习数据概览</span>
          </template>
          <div class="data-item">
            <span>累计刷题</span>
            <span class="value">{{ practiceStats.total_practice || 0 }} 道</span>
          </div>
          <div class="data-item">
            <span>总体正确率</span>
            <span class="value">{{ practiceStats.accuracy || 0 }}%</span>
          </div>
          <div class="data-item">
            <span>累计学习时长</span>
            <span class="value">{{ Math.floor((practiceStats.total_study_time || 0) / 60) }} 分钟</span>
          </div>
          <div class="data-item">
            <span>今日刷题</span>
            <span class="value">{{ practiceStats.today_count || 0 }} 道</span>
          </div>
        </el-card>
      </el-col>

      <!-- 设置区域 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <span class="card-title">个人信息设置</span>
          </template>

          <el-form :model="profileForm" label-width="100px" style="max-width: 500px">
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateProfile" :loading="updating">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span class="card-title">修改密码</span>
          </template>

          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px" style="max-width: 500px">
            <el-form-item label="原密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import { ElMessage, ElForm } from 'element-plus'
import api from '@/utils/request'

const userStore = useUserStore()
const passwordFormRef = ref(null)
const updating = ref(false)
const changingPassword = ref(false)

const profileForm = ref({
  nickname: ''
})

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const practiceStats = ref({})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loadStats = async () => {
  try {
    const res = await api.get('/practice/statistics')
    if (res.code === 200) {
      practiceStats.value = res.data
    }
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

const updateProfile = async () => {
  updating.value = true
  try {
    const res = await api.post('/auth/update-profile', profileForm.value)
    if (res.code === 200) {
      ElMessage.success('更新成功')
      await userStore.fetchUserInfo()
    }
  } catch (error) {
    console.error('更新失败', error)
    ElMessage.error('更新失败，请重试')
  } finally {
    updating.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      try {
        const res = await api.post('/auth/change-password', {
          old_password: passwordForm.value.oldPassword,
          new_password: passwordForm.value.newPassword
        })
        if (res.code === 200) {
          ElMessage.success('密码修改成功')
          passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
        }
      } catch (error) {
        console.error('修改密码失败', error)
      } finally {
        changingPassword.value = false
      }
    }
  })
}

onMounted(() => {
  if (userStore.userInfo) {
    profileForm.value.nickname = userStore.userInfo.nickname || ''
  }
  loadStats()
})
</script>

<style scoped>
.profile {
  padding: 10px;
}

.page-title {
  margin: 0 0 20px;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.user-card {
  text-align: center;
}

.user-avatar {
  margin-bottom: 20px;
}

.user-info h3 {
  margin: 0 0 15px;
  font-size: 20px;
}

.user-info p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.data-item:last-child {
  border-bottom: none;
}

.data-item .value {
  font-weight: 600;
  color: #409EFF;
}
</style>
