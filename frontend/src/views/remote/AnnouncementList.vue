<script setup lang="ts">
</script>

<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">公告管理</span>
        <el-button type="primary" @click="showCreate = true">新建公告</el-button>
      </div>
      <el-table :data="announcements" v-loading="loading">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="is_sticky" label="置顶" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_sticky ? 'danger' : 'info'">{{ row.is_sticky ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_at" label="生效时间" width="180" />
        <el-table-column prop="end_at" label="结束时间" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" :title="editMode ? '编辑公告' : '新建公告'" width="800px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入公告标题" style="width: 400px" />
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="form.is_sticky" />
        </el-form-item>
        <el-form-item label="生效时间">
          <el-date-picker v-model="form.start_at" type="datetime" placeholder="选择开始时间" style="width: 240px" />
          <span style="margin: 0 10px">至</span>
          <el-date-picker v-model="form.end_at" type="datetime" placeholder="选择结束时间" style="width: 240px" />
        </el-form-item>
        <el-form-item label="公告内容" required>
          <div ref="editorRef" style="border: 1px solid #dcdfe6; border-radius: 4px"></div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAnnouncement, getAnnouncements, deleteAnnouncement } from '@/api/remote'

const loading = ref(false)
const announcements = ref<any[]>([])
const showCreate = ref(false)
const editMode = ref(false)
const editorRef = ref<HTMLElement>()
let editor: any = null

const form = ref({
  title: '',
  is_sticky: false,
  start_at: null,
  end_at: null,
  content: '',
})

onMounted(() => {
  loadAnnouncements()
  initEditor()
})

async function loadAnnouncements() {
  loading.value = true
  announcements.value = await getAnnouncements()
  loading.value = false
}

function initEditor() {
  // 简化版：使用 textarea 替代富文本
  if (editorRef.value) {
    editorRef.value.innerHTML = `<textarea v-model="form.content" style="width: 100%; height: 300px;" placeholder="请输入公告内容（支持 HTML）"></textarea>`
  }
}

async function handleSubmit() {
  if (!form.value.title) {
    ElMessage.warning('请输入标题')
    return
  }
  
  await createAnnouncement(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  form.value = { title: '', is_sticky: false, start_at: null, end_at: null, content: '' }
  loadAnnouncements()
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除此公告？', '警告', { type: 'warning' })
  await deleteAnnouncement(row.id)
  ElMessage.success('已删除')
  loadAnnouncements()
}

function handleEdit(row: any) {
  form.value = { ...row }
  editMode.value = true
  showCreate.value = true
}
</script>

<style scoped>
.content {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.title {
  font-size: 18px;
  font-weight: bold;
}
</style>
