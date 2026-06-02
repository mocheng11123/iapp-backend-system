<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">用户反馈</span>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="loadFeedbacks" style="width: 150px">
          <el-option label="待处理" :value="0" />
          <el-option label="已读" :value="1" />
          <el-option label="已解决" :value="2" />
          <el-option label="已忽略" :value="3" />
        </el-select>
      </div>
      <el-table :data="feedbacks" v-loading="loading">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="['info', 'primary', 'success', 'warning'][row.status]">
              {{ ['待处理', '已读', '已解决', '已忽略'][row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="180" />
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" @click="handleReply(row)">回复</el-button>
            <el-button size="small" type="success" @click="handleResolve(row)">解决</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDetail" title="反馈详情" width="600px">
      <el-descriptions :column="1" v-if="currentFeedback">
        <el-descriptions-item label="标题">{{ currentFeedback.title }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentFeedback.username }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag>{{ ['待处理', '已读', '已解决', '已忽略'][currentFeedback.status] }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="内容">{{ currentFeedback.content }}</el-descriptions-item>
        <el-descriptions-item label="图片" v-if="currentFeedback.images?.length">
          <div style="display: flex; gap: 10px">
            <el-image v-for="(img, i) in currentFeedback.images" :key="i" :src="img" style="width: 100px; height: 100px" fit="cover" />
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="回复" v-if="currentFeedback.reply_content">
          {{ currentFeedback.reply_content }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="showReply" title="回复反馈" width="500px">
      <el-input v-model="replyContent" type="textarea" :rows="4" placeholder="输入回复内容" />
      <template #footer>
        <el-button @click="showReply = false">取消</el-button>
        <el-button type="primary" @click="submitReply">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/request'

const loading = ref(false)
const feedbacks = ref<any[]>([])
const statusFilter = ref<number>()
const showDetail = ref(false)
const showReply = ref(false)
const currentFeedback = ref<any>(null)
const replyContent = ref('')

onMounted(loadFeedbacks)

async function loadFeedbacks() {
  loading.value = true
  feedbacks.value = await api.get('/dev/feedback', { params: { status: statusFilter.value } })
  loading.value = false
}

function handleView(row: any) {
  currentFeedback.value = row
  showDetail.value = true
}

function handleReply(row: any) {
  currentFeedback.value = row
  replyContent.value = row.reply_content || ''
  showReply.value = true
}

async function submitReply() {
  await api.post(`/dev/feedback/${currentFeedback.value.id}/reply`, { reply_content: replyContent.value })
  ElMessage.success('已回复')
  showReply.value = false
  loadFeedbacks()
}

async function handleResolve(row: any) {
  await api.put(`/dev/feedback/${row.id}/status`, { status: 2 })
  ElMessage.success('已标记为已解决')
  loadFeedbacks()
}
</script>

<style scoped>
.content { padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { font-size: 18px; font-weight: bold; }
</style>
