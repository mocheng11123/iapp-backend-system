<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">广告配置</span>
        <el-button type="primary" @click="showCreate = true">新建广告</el-button>
      </div>
      <el-table :data="ads" v-loading="loading">
        <el-table-column prop="slot" label="广告位" width="150" />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag>{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="media_url" label="媒体链接" :show-overflow-tooltip="true" />
        <el-table-column prop="target_url" label="跳转链接" :show-overflow-tooltip="true" width="200" />
        <el-table-column prop="weight" label="权重" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleToggleStatus(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="新建广告" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="广告位" required>
          <el-input v-model="form.slot" placeholder="如：home_banner" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type">
            <el-option label="图片" value="image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="媒体链接" required>
          <el-input v-model="form.media_url" placeholder="图片或视频 URL" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.target_url" placeholder="点击后跳转地址" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="form.weight" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
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
import { createAd, getAds } from '@/api/remote'

const loading = ref(false)
const ads = ref<any[]>([])
const showCreate = ref(false)

const form = ref({
  slot: '',
  type: 'image',
  media_url: '',
  target_url: '',
  weight: 0,
  status: 1,
})

onMounted(async () => {
  loading.value = true
  ads.value = await getAds()
  loading.value = false
})

async function handleSubmit() {
  await createAd(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  form.value = { slot: '', type: 'image', media_url: '', target_url: '', weight: 0, status: 1 }
  ads.value = await getAds()
}

async function handleToggleStatus(row: any) {
  row.status = row.status === 1 ? 0 : 1
  ElMessage.success('已更新')
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？', '警告', { type: 'warning' })
  ads.value = ads.value.filter(a => a.id !== row.id)
  ElMessage.success('已删除')
}
</script>

<style scoped>
.content { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { font-size: 18px; font-weight: bold; }
</style>
