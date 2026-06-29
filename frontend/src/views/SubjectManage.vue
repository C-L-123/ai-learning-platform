<template>
  <div class="subject-manage">
    <div class="page-header">
      <h2 class="page-title">科目管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon>
        新增科目
      </el-button>
    </div>

    <el-card>
      <el-table :data="subjectList" style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="name" label="科目名称" width="120" />
        <el-table-column label="知识点关键词" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="kw in row.keywords"
              :key="kw"
              size="small"
              style="margin: 2px 4px 2px 0"
            >
              {{ kw }}
            </el-tag>
            <span v-if="!row.keywords || row.keywords.length === 0" style="color: #909399">暂无关键词</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" width="150" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              link size="small"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" @click="deleteSubject(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑科目' : '新增科目'"
      width="600px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="科目名称" required>
          <el-input v-model="formData.name" placeholder="如：生物、历史、地理" />
        </el-form-item>
        <el-form-item label="科目描述">
          <el-input v-model="formData.description" placeholder="如：高中生物" />
        </el-form-item>
        <el-form-item label="知识点关键词">
          <div style="width: 100%">
            <div style="margin-bottom: 10px">
              <el-tag
                v-for="(kw, index) in formData.keywords"
                :key="index"
                closable
                style="margin: 0 6px 6px 0"
                @close="removeKeyword(index)"
              >
                {{ kw }}
              </el-tag>
            </div>
            <div style="display: flex; gap: 10px">
              <el-input
                v-model="newKeyword"
                placeholder="输入知识点关键词"
                @keyup.enter="addKeyword"
                style="flex: 1"
              />
              <el-button @click="addKeyword" :disabled="!newKeyword.trim()">添加</el-button>
            </div>
            <div style="margin-top: 8px; color: #909399; font-size: 12px">
              提示：输入关键词后按回车或点击添加，关键词用于 OCR 试卷分析时自动识别知识点
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const subjectList = ref([])
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const newKeyword = ref('')

const formData = ref({
  name: '',
  description: '',
  keywords: []
})

const loadSubjects = async () => {
  try {
    const res = await api.get('/subject/all')
    if (res.code === 200) {
      subjectList.value = res.data
    }
  } catch (error) {
    console.error('加载科目失败', error)
  }
}

const openAddDialog = () => {
  isEdit.value = false
  editId.value = null
  formData.value = { name: '', description: '', keywords: [] }
  newKeyword.value = ''
  showDialog.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  formData.value = {
    name: row.name,
    description: row.description || '',
    keywords: [...(row.keywords || [])]
  }
  newKeyword.value = ''
  showDialog.value = true
}

const addKeyword = () => {
  const kw = newKeyword.value.trim()
  if (kw && !formData.value.keywords.includes(kw)) {
    formData.value.keywords.push(kw)
  }
  newKeyword.value = ''
}

const removeKeyword = (index) => {
  formData.value.keywords.splice(index, 1)
}

const submitForm = async () => {
  if (!formData.value.name.trim()) {
    ElMessage.warning('请输入科目名称')
    return
  }

  submitting.value = true
  try {
    let res
    if (isEdit.value) {
      res = await api.post(`/subject/update/${editId.value}`, formData.value)
    } else {
      res = await api.post('/subject/add', formData.value)
    }
    if (res.code === 200) {
      ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
      showDialog.value = false
      loadSubjects()
    }
  } catch (error) {
    console.error('提交失败', error)
  } finally {
    submitting.value = false
  }
}

const toggleActive = async (row) => {
  try {
    const res = await api.post(`/subject/update/${row.id}`, {
      is_active: !row.is_active
    })
    if (res.code === 200) {
      ElMessage.success(row.is_active ? '已禁用' : '已启用')
      loadSubjects()
    }
  } catch (error) {
    console.error('操作失败', error)
  }
}

const deleteSubject = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个科目吗？删除后相关功能可能受影响。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await api.delete(`/subject/delete/${id}`)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadSubjects()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

onMounted(() => {
  loadSubjects()
})
</script>

<style scoped>
.subject-manage {
  padding: 10px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}
</style>
