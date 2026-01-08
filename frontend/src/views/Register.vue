<template>
  <div class="register-container">
    <el-card class="register-box">
      <template #header><b>新用户注册</b></template>
      <el-form :model="form" label-width="80px" label-position="left">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学号/工号"><el-input v-model="form.student_id" /></el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="设置密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>

        <el-form-item label="身份角色">
          <el-radio-group v-model="form.role">
            <el-radio label="student">学生</el-radio>
            <el-radio label="teacher">辅导员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider content-position="left">组织信息</el-divider>

        <el-form-item label="学院"><el-input v-model="form.college" placeholder="如：计算机学院" /></el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="专业"><el-input v-model="form.major" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级"><el-input v-model="form.class_name" /></el-form-item>
          </el-col>
        </el-row>

        <el-button type="primary" @click="handleRegister" style="width: 100%; margin-top: 20px">立即注册</el-button>
        <el-button link @click="$router.push('/login')" style="width: 100%; margin-top: 10px">返回登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import request from '../utils/request'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = reactive({
  username: '', password: '', role: 'student',
  student_id: '', college: '', major: '', class_name: ''
})

const handleRegister = async () => {
  try {
    // 调用刚才在 UserViewSet 注册的 create 接口
    await request.post('/auth/users/', form)
    ElMessage.success('注册成功！')
    router.push('/login')
  } catch (err) {
    // 错误处理由 request.js 的拦截器完成
  }
}
</script>

<style scoped>
.register-container {
  background: #f5f7fa;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background-image: url('/login-bg.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.register-box {
  width: 100%;
  max-width: 550px;
  background-color: rgba(255, 255, 255, 0.9);
}
</style>