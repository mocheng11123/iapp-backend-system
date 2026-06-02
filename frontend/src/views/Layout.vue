<template>
  <div class="layout">
    <el-container>
      <el-aside width="220px">
        <div class="logo">iApp 管理控制台</div>
        <el-menu :default-active="$route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF">
          <el-menu-item index="/dashboard">
            <el-icon><DataLine /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/apps">
            <el-icon><SetUp /></el-icon>
            <span>应用管理</span>
          </el-menu-item>
          <el-menu-item index="/cards">
            <el-icon><Ticket /></el-icon>
            <span>卡密管理</span>
          </el-menu-item>
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <span>终端用户</span>
          </el-menu-item>
          <el-sub-menu index="remote">
            <template #title>
              <el-icon><Bell /></el-icon>
              <span>远程管理</span>
            </template>
            <el-menu-item index="/announcements">公告管理</el-menu-item>
            <el-menu-item index="/versions">版本管理</el-menu-item>
            <el-menu-item index="/splash">启动图</el-menu-item>
            <el-menu-item index="/ads">广告位</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/forum">
            <el-icon><ChatDotRound /></el-icon>
            <span>论坛管理</span>
          </el-menu-item>
          <el-menu-item index="/feedback">
            <el-icon><Message /></el-icon>
            <span>反馈管理</span>
          </el-menu-item>
          <el-menu-item index="/billing">
            <el-icon><Document /></el-icon>
            <span>账单管理</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-container>
        <el-header>
          <div class="header-content">
            <breadcrumb />
            <div class="user-info">
              <el-dropdown @command="handleCommand">
                <span class="user-name">
                  {{ authStore.user?.email }}
                  <el-icon><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import Breadcrumb from '@/components/Breadcrumb.vue'

const authStore = useAuthStore()
const router = useRouter()

function handleCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.el-aside {
  background-color: #304156;
  color: #fff;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  background-color: #2b3849;
}
.el-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}
.user-info {
  display: flex;
  align-items: center;
}
.user-name {
  cursor: pointer;
}
.el-main {
  background-color: #f0f2f5;
}
</style>
