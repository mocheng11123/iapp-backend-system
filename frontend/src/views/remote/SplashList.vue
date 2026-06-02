<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">启动图配置</span>
        <el-button type="primary" @click="showCreate = true">新建配置</el-button>
      </div>
      <el-table :data="splashes" v-loading="loading">
        <el-table-column prop="image_url" label="图片" width="120">
          <template #default="{ row }">
            <el-image :src="row.image_url" style="width: 80px; height: 60px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.platform }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" />
        <el-table-column prop="start_at" label="生效时间" width="180" />
        <el-table-column prop="end_at" label="结束时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="新建启动图" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="图片 URL" required>
          <el-input v-model="form.image_url" placeholder="图片地址" />
          <el-upload drag :auto-upload="false" style="margin-top: 10px">
            <el-icon><Upload /></el-icon>
            <div>选择图片后显示 URL（需配合 OSS）</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="平台" required>
          <el-select v-model="form.platform">
            <el-option label="全部" value="all" />
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" />
        </el-form-item>
        <el-form-item label="生效时间">
          <el-date-picker v-model="form.start_at" type="datetime" placeholder="开始" style="width: 180px" />
          <span style="margin: 0 10px">至</span>
          <el-date-picker v-model="form.end_at" type="datetime" placeholder="结束" style="width: 180px" />
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
import { createSplash, getSplashes } from '@/api/remote'

const loading = ref(false)
const splashes = ref<any[]>([])
const showCreate = ref(false)

const form = ref({
  image_url: '',
  platform: 'all',
  priority: 0,
  start_at: null,
  end_at: null,
})

onMounted(async () => {
  loading.value = true
  splashes.value = await getSplashes()
  loading.value = false
})

async function handleSubmit() {
  await createSplash(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  form.value = { image_url: '', platform: 'all', priority: 0, start_at: null, end_at: null }
  splashes.value = await getSplashes()
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？', '警告', { type: 'warning' })
  splashes.value = splashes.value.filter(s => s.id !== row.id)
  ElMessage.success('已删除')
}
</script>

<style scoped>
.content { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { font-size: 18px; font-weight: bold; }
</style>
