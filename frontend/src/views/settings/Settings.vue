<template>
  <div class="content">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>
      <el-tabs>
        <el-tab-pane label="Webhook 配置">
          <webhook-tab />
        </el-tab-pane>
        <el-tab-pane label="通知设置">
          <notification-tab />
        </el-tab-pane>
        <el-tab-pane label="安全设置">
          <security-tab />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { ElMessage } from 'element-plus'

function WebhookTab() {
  const webhooks = ref<any[]>([])
  const showCreate = ref(false)
  const form = ref({ url: '', events: [], retry_count: 3, retry_interval: 60 })
  
  onMounted(async () => {
    webhooks.value = await api.get('/dev/webhooks')
  })
  
  return () => h('div', { class: 'tab-content' }, [
    h('div', { class: 'tab-header', style: 'margin-bottom: 15px' }, [
      h('span', {}, 'Webhook 配置'),
      h('el-button', { type: 'primary', size: 'small', onClick: () => showCreate.value = true }, '新建 Webhook'),
    ]),
    h('el-table', { data: webhooks.value }, [
      h('el-table-column', { prop: 'url', label: 'URL', 'show-overflow-tooltip': 'true' }),
      h('el-table-column', { prop: 'events', label: '事件', width: '200' }, {
        default: ({ row }: any) => row.events?.join(', '),
      }),
      h('el-table-column', { label: '操作', width: '180' }, {
        default: () => [
          h('el-button', { size: 'small' }, '编辑'),
          h('el-button', { size: 'small', type: 'danger' }, '删除'),
        ],
      }),
    ]),
    h('el-dialog', { 'v-model': showCreate.value, title: '新建 Webhook', width: '600px' }, () => [
      h('el-form', { model: form.value, 'label-width': '100px' }, [
        h('el-form-item', { label: 'URL' }, h('el-input', { vModel: form.value.url, placeholder: 'https://your-domain.com/webhook' })),
        h('el-form-item', { label: '事件' }, h('el-checkbox-group', { modelValue: form.value.events }, [
          h('el-checkbox', { label: 'user.created' }, '用户创建'),
          h('el-checkbox', { label: 'user.balance.changed' }, '余额变动'),
          h('el-checkbox', { label: 'user.login' }, '用户登录'),
        ])),
        h('el-form-item', { label: '重试次数' }, h('el-input-number', { vModel: form.value.retry_count, min: 1, max: 10 })),
      ]),
      h('template', { '#footer' }, [
        h('el-button', { onClick: () => showCreate.value = false }, '取消'),
        h('el-button', { type: 'primary', onClick: () => ElMessage.success('创建成功') }, '提交'),
      ]),
    ]),
  ])
}

function NotificationTab() {
  const emailForm = ref({ feedback_email: '', enable_notification: true, low_balance_threshold: 10 })
  
  return () => h('div', { class: 'tab-content' }, [
    h('el-form', { model: emailForm.value, 'label-width': '150px' }, [
      h('el-form-item', { label: '反馈通知邮箱' }, h('el-input', { vModel: emailForm.value.feedback_email, placeholder: 'developer@example.com' })),
      h('el-form-item', { label: '启用通知' }, h('el-switch', { vModel: emailForm.value.enable_notification })),
      h('el-form-item', { label: '余额预警阈值' }, h('el-input-number', { vModel: emailForm.value.low_balance_threshold, min: 0 })),
      h('el-form-item', {}, h('el-button', { type: 'primary', onClick: () => ElMessage.success('保存成功') }, '保存设置')),
    ]),
  ])
}

function SecurityTab() {
  const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })
  
  return () => h('div', { class: 'tab-content' }, [
    h('el-form', { model: pwdForm.value, 'label-width': '150px' }, [
      h('el-form-item', { label: '当前密码' }, h('el-input', { type: 'password', vModel: pwdForm.value.old_password })),
      h('el-form-item', { label: '新密码' }, h('el-input', { type: 'password', vModel: pwdForm.value.new_password })),
      h('el-form-item', { label: '确认密码' }, h('el-input', { type: 'password', vModel: pwdForm.value.confirm_password })),
      h('el-form-item', {}, h('el-button', { type: 'primary', onClick: () => ElMessage.success('密码修改成功') }, '修改密码')),
    ]),
  ])
}
</script>

<style scoped>
.content { padding: 20px; }
.card-header { font-size: 16px; font-weight: bold; }
.tab-content { padding: 20px 0; max-width: 600px; }
.tab-header { display: flex; justify-content: space-between; align-items: center; }
</style>
