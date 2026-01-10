<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-circle">
          <el-icon :size="30" color="#fff"><School /></el-icon>
        </div>
        <h2>学生事务管理系统</h2>
        <p class="subtitle">Student Affairs Management System</p>
      </div>

      <el-form :model="form" @keyup.enter="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名 / 手机号"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>

        <div class="action-bar">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <el-link type="primary" :underline="false" @click="$router.push('/reset-password')">忘记密码？</el-link>
        </div>

        <el-button
          type="primary"
          :loading="loading"
          class="submit-btn"
          @click="handleLogin"
        >
          立即登录
        </el-button>

        <div class="login-footer">
          <span>还没有账号？</span>
          <el-link type="primary" @click="$router.push('/register')">点击注册</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../store/user';
import { User, Lock, School } from '@element-plus/icons-vue'; // 新增 School 图标
import { ElMessage } from 'element-plus';

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const rememberMe = ref(false);

const form = reactive({
  username: '',
  password: ''
});

const handleLogin = async () => {
  if (!form.username || !form.password) return ElMessage.warning('请输入账号密码');

  loading.value = true;
  try {
    const res = await userStore.login(form);
    ElMessage.success('欢迎回来！');

    const routes = {
      admin: '/admin-dashboard',
      teacher: '/teacher-dashboard',
      student: '/student-dashboard'
    };
    router.push(routes[res.role] || '/');
  } catch (error) {
    ElMessage.error(error.message || '登录失败');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 背景容器：渐变 + 背景图混用 */
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(103, 194, 58, 0.1) 100%),
              url('/login-bg.jpg');
  background-size: cover;
  background-position: center;
  position: relative;
}

/* 磨砂玻璃卡片 */
.login-card {
  width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px); /* 磨砂核心代码 */
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* 顶部样式 */
.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-circle {
  width: 60px;
  height: 60px;
  background: #409EFF;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto 15px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

h2 {
  color: #303133;
  font-size: 24px;
  margin: 0;
  letter-spacing: 1px;
}

.subtitle {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
  text-transform: uppercase;
}

/* 表单细节 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(90deg, #409EFF, #3a8ee6);
  border: none;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(64, 158, 255, 0.4);
}

.login-footer {
  margin-top: 25px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

/* 移动端适配 */
@media (max-width: 480px) {
  .login-card {
    width: 90%;
    padding: 30px 20px;
  }
}
</style>