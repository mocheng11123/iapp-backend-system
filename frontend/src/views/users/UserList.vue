<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">终端用户管理</span>
        <div class="actions">
          <el-select v-model="selectedApp" placeholder="选择应用" clearable @change="loadUsers" style="width: 200px">
            <el-option v-for="app in apps" :key="app.id" :label="app.name" :value="app.id" />
          </el-select>
          <el-input v-model="search" placeholder="搜索用户名" prefix-icon="Search" style="width: 200px; margin: 0 10px" @clear="loadUsers" @keyup.enter="loadUsers" />
          <el-button type="primary" @click="loadUsers">查询</el-button>
          <el-button @click="handleExport">导出</el-button>
        </div>
      </div>
      
      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="id" label="用户 ID" width="280" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 0 ? 'success' : 'danger'">
              {{ row.status === 0 ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="custom_data" label="自定义数据" width="150" :show-overflow-tooltip="true">
          <template #default="{ row }">
            {{ JSON.stringify(row.custom_data) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewDetail(row)">详情</el-button>
            <el-button size="small" :type="row.status === 0 ? 'warning' : 'success'" @click="handleToggleStatus(row)">
              {{ row.status === 0 ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadUsers" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/request'
import { getApps } from '@/api/app'

const loading = ref(false)
const users = ref<any[]>([])
const apps = ref<any[]>([])
const selectedApp = ref<string>()
const search = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

onMounted(async () => {
  apps.value = await getApps()
  loadUsers()
})

async function loadUsers() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (selectedApp.value) params.app_id = selectedApp.value
    if (search.value) params.search = search.value
    
    const res = await api.get('/api/v1/users', { params })
    users.value = res
    total.value = res.length
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleToggleStatus(row: any) {
  try {
    const enable = row.status === 1
    await api.post(`/api/v1/users/${row.id}/disable`, null, { params: { enable } })
    ElMessage.success(`${enable ? '启用' : '禁用'}成功`)
    loadUsers()
  } catch (e) {}
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定删除此用户？', '警告', { type: 'warning' })
    await api.delete(`/api/v1/users/${row.id}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e) {}
}

function handleViewDetail(row: any) {
  ElMessageBox.alert(`用户 ID: ${row.id}\n用户名：${row.username}\n状态：${row.status === 0 ? '正常' : '禁用'}`, '用户详情')
}

function handleExport() {
  window.open(`/api/v1/users/export?format=csv`, '_blank')
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
.actions {
  display: flex;
  align-items: center;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
