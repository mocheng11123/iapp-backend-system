<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">应用列表</span>
        <el-button type="primary" @click="showCreate = true">新建应用</el-button>
      </div>
      <el-table :data="apps" style="width: 100%">
        <el-table-column prop="name" label="应用名称" />
        <el-table-column prop="api_key_prefix" label="API Key" width="200" />
        <el-table-column prop="allow_enduser_login" label="允许登录" width="100">
          <template #default="{ row }">
            <el-tag :type="row.allow_enduser_login ? 'success' : 'info'">
              {{ row.allow_enduser_login ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/apps/${row.id}`)">配置</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="创建应用" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="应用名称">
          <el-input v-model="form.name" placeholder="请输入应用名称" />
        </el-form-item>
        <el-form-item label="允许登录">
          <el-switch v-model="form.allow_enduser_login" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getApps, createApp, deleteApp } from '@/api/app'
import { ElMessage } from 'element-plus'

const apps = ref<any[]>([])
const showCreate = ref(false)
const form = ref({ name: '', allow_enduser_login: false })

onMounted(async () => {
  apps.value = await getApps()
})

async function handleCreate() {
  try {
    const res = await createApp(form.value)
    ElMessage.success(`创建成功！API Key: ${res.api_key}`)
    showCreate.value = false
    apps.value = await getApps()
  } catch (e) {}
}

async function handleDelete(row: any) {
  await deleteApp(row.id)
  apps.value = apps.value.filter(a => a.id !== row.id)
  ElMessage.success('已删除')
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
