<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">版本管理</span>
        <el-button type="primary" @click="showCreate = true">新建版本</el-button>
      </div>
      <el-table :data="versions" v-loading="loading">
        <el-table-column prop="version_code" label="版本号" width="100" />
        <el-table-column prop="version_name" label="版本名称" width="120" />
        <el-table-column prop="update_log" label="更新日志" :show-overflow-tooltip="true" />
        <el-table-column prop="force_update" label="强制更新" width="100">
          <template #default="{ row }">
            <el-tag :type="row.force_update ? 'danger' : 'info'">{{ row.force_update ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="download_url" label="下载链接" :show-overflow-tooltip="true" width="300" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="新建版本" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="版本号" required>
          <el-input-number v-model="form.version_code" :min="1" style="width: 150px" />
        </el-form-item>
        <el-form-item label="版本名称" required>
          <el-input v-model="form.version_name" placeholder="如：1.0.0" style="width: 200px" />
        </el-form-item>
        <el-form-item label="更新日志" required>
          <el-input v-model="form.update_log" type="textarea" :rows="4" placeholder="请输入更新内容" />
        </el-form-item>
        <el-form-item label="下载链接" required>
          <el-input v-model="form.download_url" placeholder="APK 或 IPA 直链" />
        </el-form-item>
        <el-form-item label="文件 MD5">
          <el-input v-model="form.file_md5" placeholder="可选，自动计算" />
        </el-form-item>
        <el-form-item label="强制更新">
          <el-switch v-model="form.force_update" />
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
import { createVersion, getVersions, deleteVersion } from '@/api/remote'

const loading = ref(false)
const versions = ref<any[]>([])
const showCreate = ref(false)

const form = ref({
  version_code: 1,
  version_name: '1.0.0',
  update_log: '',
  download_url: '',
  file_md5: '',
  force_update: false,
})

onMounted(async () => {
  loading.value = true
  versions.value = await getVersions()
  loading.value = false
})

async function handleSubmit() {
  await createVersion(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  form.value = { version_code: 1, version_name: '1.0.0', update_log: '', download_url: '', file_md5: '', force_update: false }
  versions.value = await getVersions()
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除此版本？', '警告', { type: 'warning' })
  await deleteVersion(row.id)
  ElMessage.success('已删除')
  versions.value = await getVersions()
}
</script>

<style scoped>
.content { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { font-size: 18px; font-weight: bold; }
</style>
