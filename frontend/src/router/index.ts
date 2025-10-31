import { createRouter, createWebHistory } from 'vue-router'
import PublicLayout from '@/layouts/PublicLayout.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import HomeView from '@/views/HomeView.vue'
import DashboardView from '@/views/dashboard/DashboardView.vue'
import ProfileView from '@/views/profile/ProfileView.vue'
import ApiHistoryView from '@/views/history/ApiHistoryView.vue'
import OrdersView from '@/views/orders/OrdersView.vue'
import KeysManagerView from '@/views/keys/KeysManagerView.vue'
import DocsView from '@/views/docs/DocsView.vue'
import NotFoundView from '@/views/errors/NotFoundView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 公共布局路由
    {
      path: '/',
      component: PublicLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView
        },
        {
          path: '/login',
          name: 'login',
          component: LoginView,
          meta: { requiresGuest: true }
        },
        {
          path: '/register',
          name: 'register',
          component: RegisterView,
          meta: { requiresGuest: true }
        }
      ]
    },
    
    // 仪表板布局路由
    {
      path: '/dashboard',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView
        },
        {
          path: 'history',
          name: 'history',
          component: ApiHistoryView
        },
        {
          path: 'orders',
          name: 'orders',
          component: OrdersView
        },
        {
          path: 'keys',
          name: 'keys',
          component: KeysManagerView
        },
        {
          path: 'docs',
          name: 'docs',
          component: DocsView
        }
      ]
    },
    
    // 404页面
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  // 检查是否需要游客身份
  if (to.meta.requiresGuest && token) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router