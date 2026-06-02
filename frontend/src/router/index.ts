import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'apps',
        name: 'Apps',
        component: () => import('@/views/apps/AppList.vue'),
        meta: { title: '应用管理' },
      },
      {
        path: 'apps/:id',
        name: 'AppDetail',
        component: () => import('@/views/apps/AppDetail.vue'),
        meta: { title: '应用详情' },
      },
      {
        path: 'cards',
        name: 'Cards',
        component: () => import('@/views/cards/CardBatchList.vue'),
        meta: { title: '卡密管理' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UserList.vue'),
        meta: { title: '终端用户' },
      },
      {
        path: 'announcements',
        name: 'Announcements',
        component: () => import('@/views/remote/AnnouncementList.vue'),
        meta: { title: '公告管理' },
      },
      {
        path: 'versions',
        name: 'Versions',
        component: () => import('@/views/remote/VersionList.vue'),
        meta: { title: '版本管理' },
      },
      {
        path: 'splash',
        name: 'Splash',
        component: () => import('@/views/remote/SplashList.vue'),
        meta: { title: '启动图配置' },
      },
      {
        path: 'ads',
        name: 'Ads',
        component: () => import('@/views/remote/AdList.vue'),
        meta: { title: '广告配置' },
      },
      {
        path: 'forum',
        name: 'Forum',
        component: () => import('@/views/forum/BoardList.vue'),
        meta: { title: '论坛管理' },
      },
      {
        path: 'feedback',
        name: 'Feedback',
        component: () => import('@/views/feedback/FeedbackList.vue'),
        meta: { title: '反馈管理' },
      },
      {
        path: 'billing',
        name: 'Billing',
        component: () => import('@/views/billing/BillingList.vue'),
        meta: { title: '账单管理' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.path !== '/login' && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router
