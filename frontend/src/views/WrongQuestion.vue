<template>
  <div class="wrong-question">
    <h2 class="page-title">错题本</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_wrong || 0 }}</div>
            <div class="stat-label">错题总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value pending">{{ stats.pending_count || 0 }}</div>
            <div class="stat-label">待复习</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value mastered">{{ stats.mastered_count || 0 }}</div>
            <div class="stat-label">已掌握</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">错题列表</span>
          <el-radio-group v-model="currentStatus" @change="loadWrongQuestions" size="small">
            <el-radio-button value="pending">待复习</el-radio-button>
            <el-radio-button value="mastered">已掌握</el-radio-button>
            <el-radio-button value="all">全部</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="wrongQuestions" style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="subject" label="科目" width="80" />
        <el-table-column prop="knowledge_point" label="知识点" width="120" />
        <el-table-column prop="content" label="题目内容" show-overflow-tooltip />
        <el-table-column prop="wrong_count" label="错误次数" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="danger" size="small">{{ row.wrong_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : 'success'" size="small">
              {{ row.status === 'pending' ? '待复习' : '已掌握' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="reviewQuestion(row)">
              复习
            </el-button>
            <el-button type="success" link size="small" @click="markMastered(row.id)">
              标记掌握
            </el-button>
            <el-button type="danger" link size="small" @click="removeQuestion(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="wrongQuestions.length === 0" description="暂无错题记录，继续加油！" />
    </el-card>

    <!-- 复习弹窗 -->
    <el-dialog v-model="showReviewDialog" title="复习错题" width="600px">
      <div v-if="currentReviewQuestion" class="review-content">
        <div class="question-info">
          <el-tag>{{ currentReviewQuestion.subject }}</el-tag>
          <el-tag type="success">{{ currentReviewQuestion.knowledge_point }}</el-tag>
        </div>
        
        <div class="question-text">
          <p><strong>题目：</strong>{{ currentReviewQuestion.content }}</p>
        </div>

        <div v-if="currentReviewQuestion.options" class="options">
          <div v-for="(opt, idx) in currentReviewQuestion.options" :key="idx" class="option">
            {{ String.fromCharCode(65 + idx) }}. {{ opt }}
          </div>
        </div>

        <div class="answer-section">
          <p><strong>你的错误答案：</strong><span class="wrong-answer">{{ currentReviewQuestion.wrong_answer }}</span></p>
          <p><strong>正确答案：</strong><span class="correct-answer">{{ currentReviewQuestion.correct_answer }}</span></p>
        </div>

        <div class="review-action">
          <el-button type="success" @click="submitReview(true)">已掌握</el-button>
          <el-button type="warning" @click="submitReview(false)">还需复习</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const currentStatus = ref('pending')
const stats = ref({})
const wrongQuestions = ref([])
const showReviewDialog = ref(false)
const currentReviewQuestion = ref(null)

const loadStats = async () => {
  try {
    const res = await api.get('/wrong-question/statistics')
    if (res.code === 200) {
      stats.value = res.data
    }
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

const loadWrongQuestions = async () => {
  try {
    const res = await api.get('/wrong-question/list', {
      params: { status: currentStatus.value }
    })
    if (res.code === 200) {
      wrongQuestions.value = res.data.list
    }
  } catch (error) {
    console.error('加载错题失败', error)
  }
}

const reviewQuestion = (row) => {
  currentReviewQuestion.value = row
  showReviewDialog.value = true
}

const submitReview = async (isMastered) => {
  try {
    const res = await api.post(`/wrong-question/review/${currentReviewQuestion.value.id}`, {
      is_correct: isMastered
    })
    if (res.code === 200) {
      ElMessage.success(isMastered ? '恭喜！已标记为掌握' : '已记录，继续加油')
      showReviewDialog.value = false
      loadStats()
      loadWrongQuestions()
    }
  } catch (error) {
    console.error('提交复习结果失败', error)
  }
}

const markMastered = async (id) => {
  try {
    const res = await api.post(`/wrong-question/mark-mastered/${id}`)
    if (res.code === 200) {
      ElMessage.success('标记成功')
      loadStats()
      loadWrongQuestions()
    }
  } catch (error) {
    console.error('标记失败', error)
  }
}

const removeQuestion = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条错题吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await api.delete(`/wrong-question/remove/${id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadStats()
      loadWrongQuestions()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

onMounted(() => {
  loadStats()
  loadWrongQuestions()
})
</script>

<style scoped>
.wrong-question {
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
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409EFF;
}

.stat-value.pending {
  color: #E6A23C;
}

.stat-value.mastered {
  color: #67C23A;
}

.stat-label {
  color: #909399;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.review-content .question-info {
  margin-bottom: 15px;
}

.review-content .question-text {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 15px;
}

.review-content .options {
  margin-bottom: 20px;
}

.review-content .option {
  padding: 8px 0;
}

.answer-section {
  padding: 15px;
  background: #fff7e6;
  border-radius: 8px;
  margin-bottom: 20px;
}

.wrong-answer {
  color: #F56C6C;
  font-weight: 600;
}

.correct-answer {
  color: #67C23A;
  font-weight: 600;
}

.review-action {
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>
