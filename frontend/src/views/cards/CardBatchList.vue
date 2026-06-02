<template>
  <div class="content">
    <el-card>
      <div class="header">
        <span class="title">卡密批次管理</span>
        <el-button type="primary" @click="showCreate = true">新建批次</el-button>
      </div>
      <el-table :data="batches">
        <el-table-column prop="name" label="批次名称" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">{{ row.type === 1 ? '额度卡密' : '会员卡密' }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="面值/天数" width="100">
          <template #default="{ row }">{{ row.type === 1 ? `¥${row.amount}` : `${row.duration_days}天` }}</template>
        </el-table-column>
        <el-table-column prop="total_quantity" label="总数" width="80" />
        <el-table-column prop="remaining_quantity" label="剩余" width="80" />
        <el-table-column prop="total_price" label="总价" width="80">
          <template #default="{ row }">¥{{ row.total_price.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleExport(row)">导出</el-button>
            <el-button size="small" type="danger" @click="handleRevoke(row)">吊销</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="创建卡密批次" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="批次名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio :label="1">额度卡密</el-radio>
            <el-radio :label="2">会员卡密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.type === 1" label="面值">
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" />
        </el-form-item>
        <el-form-item v-else label="有效天数">
          <el-input-number v-model="form.duration_days" :min="1" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.quantity" :min="1" :max="10000" />
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
import { getCardBatches, createCardBatch, exportCards, revokeBatch } from '@/api/card'
import { ElMessage } from 'element-plus'

const batches = ref<any[]>([])
const showCreate = ref(false)
const form = ref<any>({ name: '', type: 1, amount: 10, duration_days: 30, quantity: 100 })

onMounted(async () => {
  batches.value = await getCardBatches()
})

async function handleCreate() {
  await createCardBatch(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  batches.value = await getCardBatches()
}

function handleExport(row: any) {
  window.open(`/dev/card/batches/${row.id}/cards`, '_blank')
}

async function handleRevoke(row: any) {
  await revokeBatch(row.id)
  ElMessage.success('已吊销')
  batches.value = await getCardBatches()
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
