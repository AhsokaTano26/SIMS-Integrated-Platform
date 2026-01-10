import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import NotFound from '../views/NotFound.vue';

NProgress.configure({ showSpinner: false, ease: 'ease', speed: 500 });

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/student-dashboard',
    name: 'StudentDashboard',
    component: () => import('../views/StudentDashboard.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/teacher-dashboard',
    name: 'TeacherDashboard',
    component: () => import('../views/TeacherDashboard.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/',
    redirect: '/login'
  },
  // 2. 将通配符路由放在最后！
  // 这里的 pathMatch 是自定义名称，(.*)* 表示匹配任意路径
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: { requiresAuth: false }
  },
  {
  path: '/register',
  component: () => import('../views/Register.vue')
  },
  {
  path: '/admin-dashboard',
  component: () => import('../views/AdminDashboard.vue'),
  meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('../views/ResetPassword.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫：校验登录状态
router.beforeEach((to, from, next) => {
  NProgress.start()
  const token = localStorage.getItem('access_token');
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');

  if (to.meta.requiresAuth && !token) {
    next('/login');
  } else if (to.meta.role && userInfo.role !== to.meta.role && userInfo.role !== 'admin') {
    // 如果角色不匹配且不是管理员，跳回登录或提示无权访问
    next('/login');
  } else {
    next();
  }
});

router.afterEach(() => {
  NProgress.done() // 结束加载
})

export default router;