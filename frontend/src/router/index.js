import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';

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
    // 建议使用懒加载，比赛演示时性能更好
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
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫：校验登录状态
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token');
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');

  if (to.meta.requiresAuth && !token) {
    // 未登录，拦截到登录页
    next('/login');
  } else if (to.meta.role && userInfo.role !== to.meta.role && userInfo.role !== 'admin') {
    // 角色不匹配（比如学生想进教师后台），拦截
    next('/login');
  } else {
    next();
  }
});

export default router;