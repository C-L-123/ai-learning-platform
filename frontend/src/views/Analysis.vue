<template>
  <div class="analysis">
    <h2 class="page-title">AI学情分析</h2>

    <!-- AI 学习报告 -->
    <el-card class="report-card">
      <template #header>
        <div class="report-header">
          <span class="card-title">📊 AI 个性化学习报告</span>
          <el-button type="primary" size="small" @click="generateReport" :loading="reportLoading">
            {{ aiReport ? '重新生成' : '生成学习报告' }}
          </el-button>
        </div>
      </template>

      <div v-if="reportLoading" class="report-loading">
        <el-icon class="loading-icon" size="36"><Loading /></el-icon>
        <p>AI 正在分析你的学习数据，生成个性化报告...</p>
      </div>

      <div v-else-if="aiReport" class="report-content">
        <div class="report-section">
          <h4><el-icon><DataAnalysis /></el-icon> 总体评价</h4>
          <p>{{ aiReport.summary }}</p>
        </div>

        <div class="report-section">
          <h4><el-icon><TrendCharts /></el-icon> 进步与变化</h4>
          <p>{{ aiReport.progress }}</p>
        </div>

        <div class="report-section">
          <h4><el-icon><Warning /></el-icon> 薄弱知识点分析</h4>
          <p>{{ aiReport.weak_analysis }}</p>
        </div>

        <div class="report-section">
          <h4><el-icon><Opportunity /></el-icon> 学习建议</h4>
          <ul>
            <li v-for="(s, i) in aiReport.suggestions" :key="i">{{ s }}</li>
          </ul>
        </div>

        <div class="report-section">
          <h4><el-icon><Calendar /></el-icon> 下一步学习计划</h4>
          <p>{{ aiReport.study_plan }}</p>
        </div>

        <div v-if="reportStats" class="report-stats">
          <el-tag>总刷题 {{ reportStats.total_practice }} 道</el-tag>
          <el-tag type="success">正确率 {{ reportStats.overall_accuracy }}%</el-tag>
          <el-tag type="warning">{{ reportStats.mastery_count }} 个知识点</el-tag>
          <el-tag type="danger">{{ reportStats.weak_count }} 个薄弱点</el-tag>
        </div>
      </div>

      <el-empty v-else description="点击上方按钮，AI 将为你生成个性化学习报告" :image-size="80" />
    </el-card>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <span class="card-title">上传试卷进行智能分析</span>
      </template>
      
      <el-form :inline="true" class="upload-form">
        <el-form-item label="科目">
          <el-select v-model="subject" style="width: 150px">
            <el-option
              v-for="s in subjectOptions"
              :key="s.id"
              :label="s.name"
              :value="s.name"
            />
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
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row.id)">查看详情</el-button>
            <el-button type="danger" link @click="deleteHistory(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="historyTotal > historyPageSize"
        style="margin-top: 15px; justify-content: center"
        layout="total, prev, pager, next"
        :total="historyTotal"
        :page-size="historyPageSize"
        v-model:current-page="historyPage"
        @current-change="loadHistory"
      />
    </el-card>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="分析详情" width="700px">
      <div v-if="detailData">
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="试卷名称">{{ detailData.title }}</el-descriptions-item>
          <el-descriptions-item label="科目">{{ detailData.subject }}</el-descriptions-item>
          <el-descriptions-item label="分析时间">{{ detailData.created_at }}</el-descriptions-item>
          <el-descriptions-item label="知识点数量">{{ detailData.knowledge_points?.length || 0 }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 15px 0 10px">知识点掌握度</h4>
        <div ref="detailRadarRef" class="radar-chart" style="height: 280px"></div>

        <h4 style="margin: 15px 0 10px">薄弱知识点</h4>
        <div v-if="detailData.weak_points?.length > 0">
          <el-tag v-for="point in detailData.weak_points" :key="point" type="danger" style="margin: 5px">{{ point }}</el-tag>
        </div>
        <el-empty v-else description="暂无薄弱知识点" :image-size="60" />

        <h4 style="margin: 15px 0 10px">学习建议</h4>
        <ul style="margin: 0; padding-left: 20px; color: #606266; line-height: 2">
          <li v-for="(s, i) in detailData.suggestions" :key="i">{{ s }}</li>
        </ul>

        <h4 style="margin: 15px 0 10px">OCR识别内容</h4>
        <div style="padding: 10px; background: #f5f7fa; border-radius: 6px; max-height: 200px; overflow-y: auto; font-size: 13px; color: #606266; white-space: pre-wrap">{{ detailData.ocr_content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const router = useRouter()
const radarChartRef = ref()
const detailRadarRef = ref()
let radarChart = null
let detailRadarChart = null

const subject = ref('数学')
const paperTitle = ref('')
const uploading = ref(false)
const progress = ref(0)
const uploadStatus = ref('')
const analysisResult = ref(null)
const historyList = ref([])

const showDetailDialog = ref(false)
const detailData = ref(null)
const aiReport = ref(null)
const reportLoading = ref(false)
const reportStats = ref(null)
const historyPage = ref(1)
const historyPageSize = 10
const historyTotal = ref(0)
const subjectOptions = ref([])

const loadSubjects = async () => {
  try {
    const res = await api.get('/subject/list')
    if (res.code === 200) {
      subjectOptions.value = res.data
      if (subjectOptions.value.length > 0 && !subjectOptions.value.find(s => s.name === subject.value)) {
        subject.value = subjectOptions.value[0].name
      }
    }
  } catch (error) {
    console.error('加载科目失败', error)
  }
}

const generateReport = async () => {
  reportLoading.value = true
  try {
    const res = await api.get('/analysis/ai-report', {
      params: { subject: subject.value }
    })
    if (res.code === 200) {
      aiReport.value = res.data.report
      reportStats.value = res.data.stats
      ElMessage.success('学习报告生成成功')
    } else {
      ElMessage.error(res.message || '报告生成失败')
    }
  } catch (error) {
    console.error('生成报告失败', error)
    ElMessage.error('AI 报告生成失败，请稍后重试')
  } finally {
    reportLoading.value = false
  }
}

const uploadUrl = '/api/analysis/upload'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))
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
    const res = await api.get('/analysis/history', {
      params: { page: historyPage.value, page_size: historyPageSize }
    })
    if (res.code === 200) {
      historyList.value = res.data.list
      historyTotal.value = res.data.total
    }
  } catch (error) {
    console.error('加载历史失败', error)
    ElMessage.error('加载历史失败')
  }
}

const viewDetail = async (id) => {
  try {
    const res = await api.get(`/analysis/detail/${id}`)
    if (res.code === 200) {
      detailData.value = res.data
      showDetailDialog.value = true
      // Element Plus dialog 有动画延迟，需要等待 DOM 就绪
      await nextTick()
      setTimeout(() => renderDetailRadar(), 100)
    }
  } catch (error) {
    console.error('获取详情失败', error)
  }
}

const renderDetailRadar = () => {
  if (!detailRadarRef.value || !detailData.value?.mastery_level) return

  if (detailRadarChart) {
    detailRadarChart.dispose()
  }
  detailRadarChart = echarts.init(detailRadarRef.value)

  const mastery = detailData.value.mastery_level
  const indicators = Object.keys(mastery).map(name => ({ name, max: 100 }))
  const values = Object.values(mastery)

  detailRadarChart.setOption({
    tooltip: {},
    radar: { indicator: indicators, radius: '60%' },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '掌握度',
        areaStyle: { color: 'rgba(64, 158, 255, 0.3)' },
        lineStyle: { color: '#409EFF' },
        itemStyle: { color: '#409EFF' }
      }]
    }]
  })
}

const deleteHistory = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条分析记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await api.delete(`/analysis/delete/${id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadHistory()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

const goToPractice = () => {
  router.push('/practice')
}

const handleResize = () => {
  radarChart?.resize()
}

onMounted(() => {
  loadSubjects()
  loadHistory()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  detailRadarChart?.dispose()
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

.report-card {
  margin-bottom: 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-loading {
  text-align: center;
  padding: 30px;
  color: #909399;
}

.loading-icon {
  color: #409EFF;
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.report-content {
  line-height: 1.8;
}

.report-section {
  margin-bottom: 20px;
}

.report-section h4 {
  font-size: 15px;
  color: #303133;
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.report-section p {
  color: #606266;
  margin: 0;
  text-indent: 2em;
}

.report-section ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.report-section ul li {
  margin-bottom: 6px;
}

.report-stats {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
