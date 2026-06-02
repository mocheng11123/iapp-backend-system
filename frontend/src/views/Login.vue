<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="title">iApp 管理控制台</h2>
      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleLogin">
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" prefix-icon="Message" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="links">
        <el-link type="primary" href="/docs" target="_blank">API 文档</el-link>
        <el-link type="primary" href="#" @click="goRegister">注册账号</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElForm } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.email, form.password)
      router.push('/')
    } finally {
      loading.value = false
    }
  })
}

function goRegister() {
  window.open('/dev/register', '_blank')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
  padding: 20px;
}
.title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}
.links {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}
</style>
