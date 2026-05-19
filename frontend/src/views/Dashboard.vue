<template>
  <div class="dashboard">
    <h2 class="page-title">学习数据概览</h2>
    
    <!-- 数据卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card blue">
          <div class="stat-icon">
            <el-icon><Edit /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.total_practice || 0 }}</div>
            <div class="stat-label">累计刷题总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card green">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.overall_accuracy || 0 }}%</div>
            <div class="stat-label">总体正确率</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card orange">
          <div class="stat-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.total_study_minutes || 0 }}</div>
            <div class="stat-label">累计学习时长(分钟)</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card red">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.pending_wrong_count || 0 }}</div>
            <div class="stat-label">待复习错题</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <span class="card-title">每日刷题趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span class="card-title">薄弱知识点TOP5</span>
          </template>
          <div class="weak-points-list">
            <div v-for="(item, index) in weakPoints" :key="index" class="weak-point-item">
              <span class="rank">{{ index + 1 }}</span>
              <span class="name">{{ item.knowledge_point }}</span>
              <span class="rate" :class="getRateClass(item.mastery_rate)">
                {{ item.mastery_rate }}%
              </span>
            </div>
            <el-empty v-if="weakPoints.length === 0" description="暂无薄弱知识点" :image-size="100" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 今日学习和快捷入口 -->
    <el-row :gutter="20" class="quick-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">今日学习</span>
          </template>
          <div class="today-stats">
            <div class="today-item">
              <span class="today-label">今日刷题</span>
              <span class="today-value">{{ todayStats.practice_count || 0 }} 道</span>
            </div>
            <div class="today-item">
              <span class="today-label">今日正确率</span>
              <span class="today-value">{{ todayStats.accuracy || 0 }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">快捷入口</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/analysis')">
              <el-icon><Upload /></el-icon>
              上传试卷分析
            </el-button>
            <el-button type="success" @click="$router.push('/practice')">
              <el-icon><MagicStick /></el-icon>
              开始智能刷题
            </el-button>
            <el-button type="warning" @click="$router.push('/wrong-question')">
              <el-icon><Document /></el-icon>
              复习错题
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/utils/request'

const trendChartRef = ref()
let trendChart = null

const overview = ref({})
const todayStats = ref({})
const weakPoints = ref([])
const trendData = ref({ dates: [], practice_counts: [], accuracy_rates: [] })

const loadData = async () => {
  try {
    // 加载概览数据
    const overviewRes = await api.get('/dashboard/overview')
    if (overviewRes.code === 200) {
      overview.value = overviewRes.data.stats_cards
      todayStats.value = overviewRes.data.today_stats
    }

    // 加载趋势数据
    const trendRes = await api.get('/dashboard/daily-trend')
    if (trendRes.code === 200) {
      trendData.value = trendRes.data
      renderTrendChart()
    }

    // 加载薄弱点
    const weakRes = await api.get('/dashboard/weak-points')
    if (weakRes.code === 200) {
      weakPoints.value = weakRes.data
    }
  } catch (error) {
    console.error('加载数据失败', error)
  }
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['刷题量', '正确率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trendData.value.dates
    },
    yAxis: [
      {
        type: 'value',
        name: '刷题量',
        position: 'left'
      },
      {
        type: 'value',
        name: '正确率(%)',
        position: 'right',
        max: 100
      }
    ],
    series: [
      {
        name: '刷题量',
        type: 'bar',
        data: trendData.value.practice_counts,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '正确率',
        type: 'line',
        yAxisIndex: 1,
        data: trendData.value.accuracy_rates,
        itemStyle: {
          color: '#67C23A'
        },
        smooth: true
      }
    ]
  }

  trendChart.setOption(option)
}

const getRateClass = (rate) => {
  if (rate >= 75) return 'good'
  if (rate >= 60) return 'medium'
  return 'bad'
}

const handleResize = () => {
  trendChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 10px;
}

.page-title {
  margin: 0 0 20px;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  color: white;
}

.stat-card.blue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.green {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card.orange {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.red {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-icon {
  font-size: 40px;
  margin-right: 20px;
  opacity: 0.8;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 350px;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.chart-container {
  width: 100%;
  height: 280px;
}

.weak-points-list {
  padding: 10px 0;
}

.weak-point-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.weak-point-item:last-child {
  border-bottom: none;
}

.rank {
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background: #409EFF;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  margin-right: 12px;
}

.name {
  flex: 1;
  font-size: 14px;
}

.rate {
  font-weight: 600;
}

.rate.good {
  color: #67C23A;
}

.rate.medium {
  color: #E6A23C;
}

.rate.bad {
  color: #F56C6C;
}

.quick-row {
  margin-bottom: 20px;
}

.today-stats {
  display: flex;
  justify-content: space-around;
  padding: 20px 0;
}

.today-item {
  text-align: center;
}

.today-label {
  display: block;
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.today-value {
  font-size: 24px;
  font-weight: 600;
  color: #409EFF;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
}

.quick-actions .el-button {
  justify-content: center;
}
</style>
