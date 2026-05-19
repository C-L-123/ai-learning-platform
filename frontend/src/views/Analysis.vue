<template>
  <div class="analysis">
    <h2 class="page-title">AI学情分析</h2>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <span class="card-title">上传试卷进行智能分析</span>
      </template>
      
      <el-form :inline="true" class="upload-form">
        <el-form-item label="科目">
          <el-select v-model="subject" style="width: 150px">
            <el-option label="数学" value="数学" />
            <el-option label="英语" value="英语" />
            <el-option label="物理" value="物理" />
            <el-option label="化学" value="化学" />
          </el-select>
        </el-form-item>
        <el-form-item label="试卷名称">
          <el-input v-model="paperTitle" placeholder="请输入试卷名称" style="width: 200px" />
        </el-form-item>
      </el-form>

      <el-upload
        class="upload-demo"
        drag
        :action="uploadUrl"
        :headers="uploadHeaders"
        :data="uploadData"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
        accept="image/*"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将试卷图片拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 jpg/png/bmp 格式，单张图片不超过 16MB
          </div>
        </template>
      </el-upload>

      <el-progress v-if="uploading" :percentage="progress" :status="uploadStatus" style="margin-top: 20px" />
    </el-card>

    <!-- 分析结果 -->
    <el-card v-if="analysisResult" class="result-card">
      <template #header>
        <span class="card-title">分析结果</span>
      </template>

      <el-row :gutter="20">
        <!-- 知识点雷达图 -->
        <el-col :span="12">
          <h4 class="section-title">知识点掌握度雷达图</h4>
          <div ref="radarChartRef" class="radar-chart"></div>
        </el-col>

        <!-- 薄弱点和建议 -->
        <el-col :span="12">
          <h4 class="section-title">薄弱知识点识别</h4>
          <el-tag v-for="point in analysisResult.weak_points" :key="point" type="danger" style="margin: 5px">
            {{ point }}
          </el-tag>
          <el-empty v-if="analysisResult.weak_points.length === 0" description="暂无薄弱知识点，继续保持！" :image-size="80" />

          <h4 class="section-title" style="margin-top: 30px">学习建议</h4>
          <ul class="suggestions">
            <li v-for="(suggestion, index) in analysisResult.suggestions" :key="index">
              {{ suggestion }}
            </li>
          </ul>

          <el-button type="primary" style="margin-top: 20px" @click="goToPractice">
            <el-icon><MagicStick /></el-icon>
            针对薄弱点智能刷题
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 历史记录 -->
    <el-card class="history-card" style="margin-top: 20px">
      <template #header>
        <span class="card-title">分析历史记录</span>
      </template>

      <el-table :data="historyList" style="width: 100%">
        <el-table-column prop="title" label="试卷名称" />
        <el-table-column prop="subject" label="科目" width="100" />
        <el-table-column prop="knowledge_count" label="知识点数量" width="120" />
        <el-table-column prop="created_at" label="分析时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import api from '@/utils/request'

const router = useRouter()
const radarChartRef = ref()
let radarChart = null

const subject = ref('数学')
const paperTitle = ref('')
const uploading = ref(false)
const progress = ref(0)
const uploadStatus = ref('')
const analysisResult = ref(null)
const historyList = ref([])

const uploadUrl = '/api/analysis/upload'
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token')}`
}
const uploadData = () => ({
  subject: subject.value,
  title: paperTitle.value || '未命名试卷'
})

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt16M = file.size / 1024 / 1024 < 16

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt16M) {
    ElMessage.error('图片大小不能超过 16MB!')
    return false
  }

  uploading.value = true
  progress.value = 30
  return true
}

const handleUploadSuccess = (response) => {
  uploading.value = false
  progress.value = 100
  uploadStatus.value = 'success'
  
  if (response.code === 200) {
    ElMessage.success('分析完成！')
    analysisResult.value = response.data
    renderRadarChart()
    loadHistory()
  } else {
    ElMessage.error(response.message || '分析失败')
    uploadStatus.value = 'exception'
  }
}

const handleUploadError = () => {
  uploading.value = false
  progress.value = 100
  uploadStatus.value = 'exception'
  ElMessage.error('上传失败，请重试')
}

const renderRadarChart = () => {
  if (!radarChartRef.value || !analysisResult.value) return
  
  if (!radarChart) {
    radarChart = echarts.init(radarChartRef.value)
  }

  const mastery = analysisResult.value.mastery_level
  const indicators = Object.keys(mastery).map(name => ({
    name,
    max: 100
  }))
  const values = Object.values(mastery)

  const option = {
    tooltip: {},
    radar: {
      indicator: indicators,
      radius: '60%'
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: '掌握度',
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.3)'
            },
            lineStyle: {
              color: '#409EFF'
            },
            itemStyle: {
              color: '#409EFF'
            }
          }
        ]
      }
    ]
  }

  radarChart.setOption(option)
}

const loadHistory = async () => {
  try {
    const res = await api.get('/analysis/history')
    if (res.code === 200) {
      historyList.value = res.data.list
    }
  } catch (error) {
    console.error('加载历史失败', error)
  }
}

const viewDetail = (id) => {
  ElMessage.info('查看详情功能')
}

const goToPractice = () => {
  router.push('/practice')
}

const handleResize = () => {
  radarChart?.resize()
}

onMounted(() => {
  loadHistory()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
})
</script>

<style scoped>
.analysis {
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

.upload-form {
  margin-bottom: 20px;
}

.upload-demo {
  width: 100%;
}

.section-title {
  margin: 0 0 15px;
  font-size: 16px;
  color: #303133;
}

.radar-chart {
  width: 100%;
  height: 300px;
}

.suggestions {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 2;
}
</style>
