<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">论坛版块管理</span>
        <el-button type="primary" @click="showCreate = true">新建版块</el-button>
      </div>
      <el-table :data="boards">
        <el-table-column prop="name" label="版块名称" />
        <el-table-column prop="description" label="描述" :show-overflow-tooltip="true" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '开放' : '关闭' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewPosts(row)">帖子</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="新建版块" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="版块名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'

const boards = ref<any[]>([])
const showCreate = ref(false)

const form = ref({ name: '', description: '', sort_order: 0 })

onMounted(async () => {
  boards.value = await api.get('/dev/forum/boards')
})

async function handleSubmit() {
  await api.post('/dev/forum/boards', form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  form.value = { name: '', description: '', sort_order: 0 }
  boards.value = await api.get('/dev/forum/boards')
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？包含的帖子会被级联删除', '警告', { type: 'warning' })
  boards.value = boards.value.filter(b => b.id !== row.id)
  ElMessage.success('已删除')
}

function handleViewPosts(row: any) {
  ElMessage.info(`查看版块 "${row.name}" 的帖子（待实现）`)
}
</script>

<style scoped>
.content { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { font-size: 18px; font-weight: bold; }
</style>
