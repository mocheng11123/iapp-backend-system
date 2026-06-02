<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background: #409EFF"><el-icon><SetUp /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.total_apps || 0 }}</div>
              <div class="stat-label">应用总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background: #67C23A"><el-icon><User /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.total_users || 0 }}</div>
              <div class="stat-label">终端用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background: #E6A23C"><el-icon><DataLine /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.total_api_calls_today || 0 }}</div>
              <div class="stat-label">今日 API 调用</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background: #F56C6C"><el-icon><Money /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">¥{{ stats?.total_cost_today?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">今日消费</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>余额信息</span>
            </div>
          </template>
          <div class="balance-info">
            <div class="balance-item">
              <span class="label">可用余额：</span>
              <span class="value">¥{{ balance?.balance?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="balance-item">
              <span class="label">冻结余额：</span>
              <span class="value">¥{{ balance?.frozen_balance?.toFixed(2) || '0.00' }}</span>
            </div>
            <el-button type="primary" @click="showRecharge = true" style="margin-top: 20px">
              充值
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>费用预估</template>
          <div class="prediction-info">
            <div class="prediction-item">
              <span class="label">今日预估：</span>
              <span class="value">¥{{ prediction?.today_estimated?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="prediction-item">
              <span class="label">本月预估：</span>
              <span class="value">¥{{ prediction?.month_estimated?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="prediction-item" v-if="prediction?.days_remaining">
              <span class="label">可用天数：</span>
              <span class="value">{{ prediction.days_remaining }}天</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近 7 天 API 调用趋势</span>
            </div>
          </template>
          <div class="chart" style="height: 300px">
            <div v-for="item in stats?.api_calls_trend" :key="item.date" class="chart-bar">
              <div class="bar-label">{{ item.date }}</div>
              <div class="bar-container">
                <div class="bar" :style="{ height: getBarHeight(item.count) + 'px' }"></div>
              </div>
              <div class="bar-value">{{ item.count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showRecharge" title="充值" width="400px">
      <el-input-number v-model="rechargeAmount" :min="1" :max="100000" style="width: 200px" />
      <template #footer>
        <el-button @click="showRecharge = false">取消</el-button>
        <el-button type="primary" @click="handleRecharge">确认充值</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDashboard, getBillingPrediction } from '@/api/app'
import { getBalance, recharge } from '@/api/developer'
import { ElMessage } from 'element-plus'

const stats = ref<any>({})
const balance = ref<any>({})
const prediction = ref<any>({})
const showRecharge = ref(false)
const rechargeAmount = ref(100)

onMounted(async () => {
  const [dashboardRes, predictionRes, balanceRes] = await Promise.all([
    getDashboard(),
    getBillingPrediction(),
    getBalance(),
  ])
  stats.value = dashboardRes
  prediction.value = predictionRes
  balance.value = balanceRes
})

function getBarHeight(count: number) {
  const maxCount = Math.max(...(stats.value.api_calls_trend?.map((i: any) => i.count) || [1]))
  return (count / maxCount) * 200
}

async function handleRecharge() {
  try {
    await recharge(rechargeAmount.value)
    ElMessage.success('充值成功')
    showRecharge.value = false
    balance.value = await getBalance()
  } catch (e) {}
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}
.stat-card {
  display: flex;
  align-items: center;
}
.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28px;
  margin-right: 15px;
}
.stat-info {
  flex: 1;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}
.balance-info, .prediction-info {
  padding: 10px 0;
}
.balance-item, .prediction-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}
.label {
  color: #606266;
}
.value {
  font-weight: bold;
  color: #303133;
}
.chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  padding: 20px 0;
}
.chart-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}
.bar-container {
  width: 40px;
  height: 200px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 5px;
}
.bar {
  width: 30px;
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}
.bar-label {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
.bar-value {
  font-size: 12px;
  color: #606266;
  margin-top: 5px;
}
</style>
