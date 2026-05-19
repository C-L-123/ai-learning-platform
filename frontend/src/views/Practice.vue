<template>
  <div class="practice">
    <h2 class="page-title">智能刷题</h2>

    <!-- 筛选和开始区域 -->
    <el-card v-if="!isPracticing" class="start-card">
      <template #header>
        <span class="card-title">选择刷题模式</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="12">
          <div class="mode-card smart-mode" @click="startSmartPractice">
            <el-icon size="48"><MagicStick /></el-icon>
            <h3>智能推荐刷题</h3>
            <p>基于你的薄弱知识点智能推荐题目</p>
            <el-tag type="danger">推荐</el-tag>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="mode-card normal-mode" @click="showNormalPractice = true">
            <el-icon size="48"><List /></el-icon>
            <h3>自定义选题</h3>
            <p>按科目、知识点自主选择题目</p>
          </div>
        </el-col>
      </el-row>

      <!-- 自定义选题弹窗 -->
      <el-dialog v-model="showNormalPractice" title="自定义选题" width="500px">
        <el-form label-width="80px">
          <el-form-item label="科目">
            <el-select v-model="filter.subject" style="width: 100%">
              <el-option label="数学" value="数学" />
              <el-option label="英语" value="英语" />
              <el-option label="物理" value="物理" />
            </el-select>
          </el-form-item>
          <el-form-item label="题目数量">
            <el-input-number v-model="questionCount" :min="5" :max="50" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showNormalPractice = false">取消</el-button>
          <el-button type="primary" @click="startNormalPractice">开始刷题</el-button>
        </template>
      </el-dialog>
    </el-card>

    <!-- 刷题界面 -->
    <el-card v-if="isPracticing" class="practice-card">
      <template #header>
        <div class="practice-header">
          <span>答题进度：{{ currentIndex + 1 }} / {{ questions.length }}</span>
          <el-progress :percentage="progressPercent" :show-text="false" style="width: 200px" />
          <el-button type="danger" link @click="exitPractice">退出</el-button>
        </div>
      </template>

      <div v-if="questions.length > 0" class="question-area">
        <div class="question-info">
          <el-tag>{{ currentQuestion.subject }}</el-tag>
          <el-tag type="success">{{ currentQuestion.knowledge_point }}</el-tag>
          <span class="difficulty">难度：{{ '★'.repeat(currentQuestion.difficulty) }}</span>
        </div>

        <div class="question-content">
          <h4>{{ currentQuestion.content }}</h4>
          
          <div v-if="currentQuestion.options" class="options">
            <el-radio-group v-model="userAnswer" class="option-group">
              <el-radio
                v-for="(option, index) in currentQuestion.options"
                :key="index"
                :label="String.fromCharCode(65 + index)"
                class="option-item"
              >
                {{ String.fromCharCode(65 + index) }}. {{ option }}
              </el-radio>
            </el-radio-group>
          </div>

          <div v-else class="fill-answer">
            <el-input
              v-model="userAnswer"
              placeholder="请输入答案"
              size="large"
              style="width: 300px"
            />
          </div>
        </div>

        <!-- 答案反馈 -->
        <div v-if="showResult" class="result-area" :class="isCorrect ? 'correct' : 'wrong'">
          <el-icon size="24">{{ isCorrect ? 'CircleCheck' : 'CircleClose' }}</el-icon>
          <span>{{ isCorrect ? '回答正确！' : '回答错误' }}</span>
          <div class="answer-detail">
            <p>正确答案：<strong>{{ currentQuestion.answer }}</strong></p>
            <p v-if="currentQuestion.analysis">解析：{{ currentQuestion.analysis }}</p>
          </div>
        </div>

        <div class="action-area">
          <el-button v-if="!showResult" type="primary" size="large" @click="submitAnswer" :disabled="!userAnswer">
            提交答案
          </el-button>
          <el-button v-else type="primary" size="large" @click="nextQuestion">
            {{ currentIndex < questions.length - 1 ? '下一题' : '查看结果' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 刷题结果 -->
    <el-card v-if="showSummary" class="summary-card">
      <template #header>
        <span class="card-title">刷题完成</span>
      </template>

      <div class="summary-content">
        <div class="summary-stats">
          <div class="stat-item">
            <span class="label">总题数</span>
            <span class="value">{{ questions.length }}</span>
          </div>
          <div class="stat-item">
            <span class="label">正确</span>
            <span class="value correct">{{ correctCount }}</span>
          </div>
          <div class="stat-item">
            <span class="label">错误</span>
            <span class="value wrong">{{ wrongCount }}</span>
          </div>
          <div class="stat-item">
            <span class="label">正确率</span>
            <span class="value">{{ accuracy }}%</span>
          </div>
        </div>

        <div class="summary-actions">
          <el-button type="primary" size="large" @click="restartPractice">再来一组</el-button>
          <el-button size="large" @click="goToWrongQuestion">查看错题</el-button>
          <el-button size="large" @click="backToStart">返回</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/request'

const router = useRouter()

const isPracticing = ref(false)
const showNormalPractice = ref(false)
const showResult = ref(false)
const showSummary = ref(false)

const filter = ref({
  subject: '数学'
})
const questionCount = ref(10)
const questions = ref([])
const currentIndex = ref(0)
const userAnswer = ref('')
const isCorrect = ref(false)
const correctCount = ref(0)
const wrongCount = ref(0)

const currentQuestion = computed(() => questions.value[currentIndex.value] || {})
const progressPercent = computed(() => Math.round(((currentIndex.value + 1) / questions.value.length) * 100))
const accuracy = computed(() => questions.value.length > 0 
  ? Math.round((correctCount.value / questions.value.length) * 100) 
  : 0)

const startSmartPractice = async () => {
  try {
    const res = await api.get('/practice/smart-recommend', {
      params: { subject: filter.value.subject, count: questionCount.value }
    })
    if (res.code === 200) {
      questions.value = res.data.questions
      if (questions.value.length > 0) {
        isPracticing.value = true
        currentIndex.value = 0
        correctCount.value = 0
        wrongCount.value = 0
        ElMessage.success(`已为您智能推荐 ${questions.value.length} 道题目`)
      } else {
        ElMessage.warning('暂无可推荐的题目')
      }
    }
  } catch (error) {
    console.error('获取题目失败', error)
  }
}

const startNormalPractice = async () => {
  showNormalPractice.value = false
  await startSmartPractice()
}

const submitAnswer = async () => {
  try {
    const res = await api.post('/practice/submit-answer', {
      question_id: currentQuestion.value.id,
      answer: userAnswer.value
    })
    if (res.code === 200) {
      isCorrect.value = res.data.is_correct
      if (isCorrect.value) {
        correctCount.value++
      } else {
        wrongCount.value++
      }
      showResult.value = true
    }
  } catch (error) {
    console.error('提交答案失败', error)
  }
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    userAnswer.value = ''
    showResult.value = false
  } else {
    isPracticing.value = false
    showSummary.value = true
  }
}

const exitPractice = () => {
  isPracticing.value = false
  showResult.value = false
  userAnswer.value = ''
}

const restartPractice = () => {
  showSummary.value = false
  startSmartPractice()
}

const goToWrongQuestion = () => {
  router.push('/wrong-question')
}

const backToStart = () => {
  showSummary.value = false
  isPracticing.value = false
}
</script>

<style scoped>
.practice {
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

.mode-card {
  padding: 30px;
  text-align: center;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.mode-card:hover {
  border-color: #409EFF;
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.mode-card h3 {
  margin: 15px 0 10px;
  font-size: 18px;
}

.mode-card p {
  color: #909399;
  margin-bottom: 10px;
}

.smart-mode {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

.normal-mode {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.practice-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.question-info {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.difficulty {
  color: #E6A23C;
  margin-left: 10px;
}

.question-content h4 {
  font-size: 18px;
  line-height: 1.8;
  margin-bottom: 30px;
  font-weight: 500;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.option-item {
  font-size: 16px;
}

.result-area {
  margin: 30px 0;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.result-area.correct {
  background: #f0f9eb;
  color: #67C23A;
}

.result-area.wrong {
  background: #fef0f0;
  color: #F56C6C;
}

.answer-detail {
  margin-top: 15px;
  text-align: left;
  color: #606266;
}

.action-area {
  text-align: center;
  margin-top: 30px;
}

.summary-content {
  text-align: center;
  padding: 30px;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-bottom: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-item .label {
  color: #909399;
  font-size: 14px;
}

.stat-item .value {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
}

.stat-item .value.correct {
  color: #67C23A;
}

.stat-item .value.wrong {
  color: #F56C6C;
}

.summary-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>
