<template>
  <div class="content">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>余额信息</span>
            </div>
          </template>
          <div class="balance-info" v-if="balance">
            <el-statistic title="可用余额" :value="balance.balance" :precision="2" prefix="¥" />
            <el-divider />
            <el-statistic title="冻结余额" :value="balance.frozen_balance" :precision="2" prefix="¥" />
            <el-button type="primary" @click="showRecharge = true" style="width: 100%; margin-top: 20px">充值</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>充值记录</template>
          <el-table :data="rechargeRecords" :show-summary="false">
            <el-table-column prop="amount" label="金额">
              <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="reason" label="备注" :show-overflow-tooltip="true" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>交易流水</span>
              <el-button @click="handleExport">导出 CSV</el-button>
            </div>
          </template>
          <el-table :data="transactions">
            <el-table-column prop="amount" label="金额">
              <template #default="{ row }">
                <span :style="{ color: row.amount > 0 ? '#67C23A' : '#F56C6C' }">
                  {{ row.amount > 0 ? '+' : '' }}¥{{ row.amount.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.type === 'recharge' ? 'success' : 'warning'">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" :show-overflow-tooltip="true" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showRecharge" title="充值" width="400px">
      <div style="text-align: center; padding: 20px">
        <div style="font-size: 14px; color: #909399; margin-bottom: 20px">当前余额：¥{{ balance?.balance?.toFixed(2) }}</div>
        <div class="quick-amounts">
          <el-button @click="rechargeAmount = 100">¥100</el-button>
          <el-button @click="rechargeAmount = 500">¥500</el-button>
          <el-button @click="rechargeAmount = 1000">¥1000</el-button>
          <el-button @click="rechargeAmount = 5000">¥5000</el-button>
        </div>
        <el-input-number v-model="rechargeAmount" :min="1" :max="100000" style="margin-top: 20px; width: 200px" />
      </div>
      <template #footer>
        <el-button @click="showRecharge = false">取消</el-button>
        <el-button type="primary" @click="submitRecharge">确认充值</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getBalance, recharge, getTransactions } from '@/api/developer'

const loading = ref(false)
const balance = ref<any>(null)
const transactions = ref<any[]>([])
const rechargeRecords = ref<any[]>([])
const showRecharge = ref(false)
const rechargeAmount = ref(500)

onMounted(async () => {
  balance.value = await getBalance()
  transactions.value = await getTransactions({ limit: 50 })
  rechargeRecords.value = transactions.value.filter((t: any) => t.type === 'recharge').slice(0, 10)
})

async function submitRecharge() {
  await recharge(rechargeAmount.value)
  ElMessage.success('充值成功')
  showRecharge.value = false
  balance.value = await getBalance()
  transactions.value = await getTransactions({ limit: 50 })
  rechargeRecords.value = transactions.value.filter((t: any) => t.type === 'recharge').slice(0, 10)
}

function handleExport() {
  window.open('/dev/transactions/export', '_blank')
}
</script>

<style scoped>
.content { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.balance-info { text-align: center; }
.quick-amounts { display: flex; gap: 10px; justify-content: center; }
</style>
