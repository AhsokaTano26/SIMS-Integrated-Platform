<template>
  <div class="login-container">
    <el-card class="login-box">
      <h2>学生事务管理系统</h2>
      <el-form :model="form" @keyup.enter="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="handleLogin" style="width: 100%">登录</el-button>
        <div class="login-footer">
          <el-link type="primary" @click="$router.push('/register')">立即注册新账号</el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../store/user';
import { User, Lock } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);

const form = reactive({
  username: '',
  password: ''
});

const handleLogin = async () => {
  if (!form.username || !form.password) return ElMessage.warning('请输入账号密码');

  loading.value = true;
  try {
    const res = await userStore.login(form);
    ElMessage.success('登录成功');

    // 根据角色跳转
    if (res.role === 'admin') {
        router.push('/admin-dashboard');
    } else if (res.role === 'teacher') {
        router.push('/teacher-dashboard');
    } else {
        router.push('/student-dashboard');
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f2f5;

  background-image: url('/login-bg.jpg'); /* 替换为你的图片路径 */
  background-size: cover;          /* 使图片覆盖整个容器 */
  background-position: center;     /* 图片居中显示 */
  background-repeat: no-repeat;    /* 不重复图片 */
}
.login-box {
  width: 400px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.9);
}
h2 { margin-bottom: 30px; color: #409EFF; }
.login-footer {
  margin-top: 15px;
  text-align: center;
}
</style>