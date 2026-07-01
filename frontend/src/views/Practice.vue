<template>
  <div class="practice">
    <h2 class="page-title">智能刷题</h2>

    <!-- 筛选和开始区域 -->
    <el-card v-if="!isPracticing" class="start-card">
      <template #header>
        <span class="card-title">选择刷题模式</span>
      </template>

      <div style="margin-bottom: 20px">
        <span style="margin-right: 10px">科目：</span>
        <el-radio-group v-model="filter.subject">
          <el-radio-button
            v-for="s in subjectOptions"
            :key="s.id"
            :value="s.name"
          >
            {{ s.name }}
          </el-radio-button>
        </el-radio-group>
      </div>

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
              <el-option
                v-for="s in subjectOptions"
                :key="s.id"
                :label="s.name"
                :value="s.name"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="知识点">
            <el-input v-model="filter.knowledge_point" placeholder="可选，留空则全部" style="width: 100%" />
          </el-form-item>
          <el-form-item label="题型">
            <el-select v-model="filter.question_type" style="width: 100%">
              <el-option label="全部题型" value="" />
              <el-option label="单选题" value="单选" />
              <el-option label="解答题" value="解答" />
            </el-select>
          </el-form-item>
          <el-form-item label="难度">
            <el-select v-model="filter.difficulty" style="width: 100%">
              <el-option label="全部难度" :value="0" />
              <el-option label="⭐ 基础题" :value="1" />
              <el-option label="⭐⭐ 中等题" :value="2" />
              <el-option label="⭐⭐⭐ 高难度题" :value="3" />
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

    <!-- AI 出题 loading -->
    <el-card v-if="loadingQuestions" class="loading-card">
      <div class="loading-content">
        <el-icon class="loading-icon" size="48"><Loading /></el-icon>
        <h3>AI 正在出题中...</h3>
        <p>请稍候，正在为您生成个性化题目</p>
      </div>
    </el-card>

    <!-- 刷题界面 -->
    <el-card v-if="isPracticing" class="practice-card">
      <template #header>
        <div class="practice-header">
          <span>答题进度：{{ currentIndex + 1 }} / {{ questions.length }}</span>
          <el-progress :percentage="progressPercent" :show-text="false" style="width: 200px" />
          <span class="timer">⏱ {{ formatTime(sessionTime) }}</span>
          <el-button type="danger" link @click="exitPractice">退出</el-button>
        </div>
      </template>

      <div v-if="questions.length > 0" class="question-area">
        <div class="question-info">
          <el-tag>{{ currentQuestion.subject }}</el-tag>
          <el-tag type="success">{{ currentQuestion.knowledge_point }}</el-tag>
          <el-tag :type="currentQuestion.question_type === '解答' ? 'warning' : 'info'">{{ currentQuestion.question_type || '单选' }}</el-tag>
          <span class="difficulty">难度：{{ '★'.repeat(currentQuestion.difficulty) }}</span>
        </div>

        <div class="question-content">
          <h4 v-html="renderLatex(currentQuestion.content)"></h4>
          
          <!-- 解答题：文本输入 + 图片上传 -->
          <div v-if="currentQuestion.question_type === '解答'" class="essay-answer">
            <el-input
              v-model="userAnswer"
              type="textarea"
              :rows="5"
              placeholder="请输入你的解答..."
              size="large"
            />
            <div class="essay-upload">
              <el-upload
                :action="practiceUploadUrl"
                :headers="uploadHeaders"
                :show-file-list="false"
                :on-success="handleImageSuccess"
                :before-upload="beforeImageUpload"
                accept="image/*"
              >
                <el-button size="small" :icon="Camera">上传作答图片（可选）</el-button>
              </el-upload>
              <div v-if="uploadedImage" class="uploaded-preview">
                <el-tag type="success" closable @close="uploadedImage = ''">已上传图片</el-tag>
              </div>
            </div>
          </div>

          <!-- 选择题：选项 -->
          <div v-else-if="currentQuestion.options && currentQuestion.options.length > 0" class="options">
            <el-radio-group v-model="userAnswer" class="option-group">
              <el-radio
                v-for="(option, index) in currentQuestion.options"
                :key="index"
                :label="String.fromCharCode(65 + index)"
                class="option-item"
              >
                <span v-html="String.fromCharCode(65 + index) + '. ' + renderLatex(option)"></span>
              </el-radio>
            </el-radio-group>
          </div>

          <!-- 填空题：单行输入 -->
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
          <div class="result-header">
            <el-icon size="28"><CircleCheck v-if="isCorrect" /><CircleClose v-else /></el-icon>
            <span>{{ isCorrect ? '回答正确！' : '回答错误' }}</span>
          </div>
          <div class="answer-detail">
            <!-- 解答题：AI 点评 -->
            <template v-if="currentQuestion.question_type === '解答'">
              <div class="score-bar">
                <span>得分</span>
                <el-progress :percentage="essayScore" :color="essayScore >= 60 ? '#67C23A' : '#F56C6C'" style="flex: 1" />
                <strong>{{ essayScore }}</strong> / 100
              </div>
              <div class="feedback-box" v-if="essayFeedback">
                <p><strong>AI 点评：</strong>{{ essayFeedback }}</p>
              </div>
            </template>
            <p class="correct-answer-line">
              {{ currentQuestion.question_type === '解答' ? '参考' : '正确' }}答案：
              <el-tag :type="isCorrect ? 'success' : 'danger'" size="large">{{ currentQuestion.answer || '无' }}</el-tag>
            </p>
            <div v-if="currentQuestion.analysis" class="analysis-box">
              <h5>📖 详细解析</h5>
              <p v-html="renderLatex(currentQuestion.analysis)"></p>
            </div>
          </div>
        </div>

        <div class="action-area">
          <el-button v-if="!showResult" type="primary" size="large" @click="submitAnswer" :disabled="!userAnswer" :loading="submitting">
            {{ submitting && currentQuestion.question_type === '解答' ? 'AI 判分中...' : '提交答案' }}
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera } from '@element-plus/icons-vue'
import api from '@/utils/request'
import { renderLatex } from '@/utils/latex'

const router = useRouter()

const isPracticing = ref(false)
const showNormalPractice = ref(false)
const showResult = ref(false)
const showSummary = ref(false)
const subjectOptions = ref([])
const loadingQuestions = ref(false)

const filter = ref({
  subject: '数学',
  knowledge_point: '',
  question_type: '',
  difficulty: 0
})
const questionCount = ref(10)
const questions = ref([])
const currentIndex = ref(0)
const userAnswer = ref('')
const isCorrect = ref(false)
const correctCount = ref(0)
const wrongCount = ref(0)
const essayScore = ref(0)
const essayFeedback = ref('')
const submitting = ref(false)
const uploadedImage = ref('')

const practiceUploadUrl = '/api/practice/upload-image'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isImage) { ElMessage.error('只能上传图片文件!'); return false }
  if (!isLt10M) { ElMessage.error('图片大小不能超过 10MB!'); return false }
  return true
}

const handleImageSuccess = (response) => {
  if (response.code === 200) {
    uploadedImage.value = response.data.image_path
    ElMessage.success('图片上传成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

// 整场计时器
const sessionTime = ref(0)
const sessionStartTime = ref(0)
let timerInterval = null

const startTimer = () => {
  sessionTime.value = 0
  sessionStartTime.value = Date.now()
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    sessionTime.value = Math.floor((Date.now() - sessionStartTime.value) / 1000)
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const loadSubjects = async () => {
  try {
    const res = await api.get('/subject/list')
    if (res.code === 200) {
      subjectOptions.value = res.data
      if (subjectOptions.value.length > 0) {
        filter.value.subject = subjectOptions.value[0].name
      }
    }
  } catch (error) {
    console.error('加载科目失败', error)
  }
}

onMounted(() => {
  loadSubjects()
})

onUnmounted(() => {
  stopTimer()
})

const currentQuestion = computed(() => questions.value[currentIndex.value] || {})
const progressPercent = computed(() => Math.round(((currentIndex.value + 1) / questions.value.length) * 100))
const accuracy = computed(() => questions.value.length > 0 
  ? Math.round((correctCount.value / questions.value.length) * 100) 
  : 0)

const startSmartPractice = async () => {
  loadingQuestions.value = true
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
        startTimer()
        ElMessage.success(`AI 已为您生成 ${questions.value.length} 道题目`)
      } else {
        ElMessage.warning('AI 出题失败，请稍后重试')
      }
    } else {
      ElMessage.error(res.message || 'AI 出题失败')
    }
  } catch (error) {
    console.error('获取题目失败', error)
    ElMessage.error('AI 出题失败，请检查网络或稍后重试')
  } finally {
    loadingQuestions.value = false
  }
}

const startNormalPractice = async () => {
  showNormalPractice.value = false
  loadingQuestions.value = true
  try {
    const params = {
      subject: filter.value.subject,
      page_size: questionCount.value
    }
    if (filter.value.knowledge_point) {
      params.knowledge_point = filter.value.knowledge_point
    }
    if (filter.value.question_type) {
      params.question_type = filter.value.question_type
    }
    if (filter.value.difficulty) {
      params.difficulty = filter.value.difficulty
    }
    const res = await api.get('/practice/questions', { params })
    if (res.code === 200) {
      questions.value = res.data.list
      if (questions.value.length > 0) {
        isPracticing.value = true
        currentIndex.value = 0
        correctCount.value = 0
        wrongCount.value = 0
        startTimer()
        ElMessage.success(`AI 已生成 ${questions.value.length} 道题目`)
      } else {
        ElMessage.warning('AI 出题失败，请稍后重试')
      }
    } else {
      ElMessage.error(res.message || 'AI 出题失败')
    }
  } catch (error) {
    console.error('获取题目失败', error)
    ElMessage.error('AI 出题失败，请检查网络或稍后重试')
  } finally {
    loadingQuestions.value = false
  }
}

const submitAnswer = async () => {
  submitting.value = true
  try {
    const payload = {
      question_id: currentQuestion.value.id,
      answer: userAnswer.value
    }
    if (uploadedImage.value) {
      payload.image_path = uploadedImage.value
    }
    const res = await api.post('/practice/submit-answer', payload)
    if (res.code === 200) {
      isCorrect.value = res.data.is_correct
      essayScore.value = res.data.score || 0
      essayFeedback.value = res.data.feedback || ''
      if (isCorrect.value) {
        correctCount.value++
      } else {
        wrongCount.value++
      }
      showResult.value = true
    }
  } catch (error) {
    console.error('提交答案失败', error)
  } finally {
    submitting.value = false
  }
}

const nextQuestion = async () => {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    userAnswer.value = ''
    showResult.value = false
    uploadedImage.value = ''
  } else {
    stopTimer()
    // 记录整场学习时长
    await api.post('/practice/session-complete', {
      total_time: sessionTime.value,
      question_count: questions.value.length
    }).catch(() => {})
    isPracticing.value = false
    showSummary.value = true
  }
}

const exitPractice = () => {
  stopTimer()
  if (sessionTime.value > 0) {
    api.post('/practice/session-complete', {
      total_time: sessionTime.value,
      question_count: currentIndex.value + 1
    }).catch(() => {})
  }
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

.timer {
  font-size: 16px;
  font-weight: 600;
  color: #E6A23C;
  font-family: monospace;
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

.essay-answer {
  margin: 20px 0;
}

.essay-answer .el-textarea {
  width: 100%;
  font-size: 15px;
}

.essay-upload {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.uploaded-preview {
  display: inline-flex;
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
}

.result-area.correct {
  background: #f0f9eb;
}

.result-area.correct .result-header {
  color: #67C23A;
}

.result-area.wrong {
  background: #fef0f0;
}

.result-area.wrong .result-header {
  color: #F56C6C;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
}

.answer-detail {
  text-align: left;
  color: #303133;
}

.correct-answer-line {
  margin: 12px 0;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-box {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  border: 1px solid #e4e7ed;
}

.analysis-box h5 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #303133;
}

.analysis-box p {
  margin: 0;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0;
  font-size: 14px;
}

.feedback-box {
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  margin: 10px 0;
  line-height: 1.8;
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

.loading-card {
  margin-top: 20px;
}

.loading-content {
  text-align: center;
  padding: 40px;
}

.loading-content h3 {
  margin: 20px 0 10px;
  font-size: 18px;
  color: #303133;
}

.loading-content p {
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
</style>
