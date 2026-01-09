<template>
  <div class="reset-container">
    <el-card class="reset-box">
      <template #header><b>找回密码</b></template>
      
      <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px">
        <el-step title="身份核验" />
        <el-step title="重置密码" />
      </el-steps>

      <el-form :model="form" label-width="80px">
        <div v-if="activeStep === 0">
          <el-form-item label="学号/工号">
            <el-input v-model="form.student_id" placeholder="请输入您的学号" />
          </el-form-item>
          <el-form-item label="真实姓名">
            <el-input v-model="form.username" placeholder="请输入注册时的姓名" />
          </el-form-item>
          <el-button type="primary" @click="verifyUser" style="width: 100%">下一步</el-button>
        </div>

        <div v-if="activeStep === 1">
          <el-form-item label="新密码">
            <el-input v-model="form.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input v-model="form.confirm_password" type="password" show-password />
          </el-form-item>
          <el-button type="success" @click="submitReset" style="width: 100%">提交修改</el-button>
        </div>
      </el-form>
      
      <div style="margin-top: 15px; text-align: center;">
        <el-link type="info" @click="$router.push('/login')">返回登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '../utils/request'

const router = useRouter()
const activeStep = ref(0)
const form = reactive({
  student_id: '',
  username: '',
  new_password: '',
  confirm_password: ''
})

// 第一步：校验用户是否存在
const verifyUser = async () => {
  if (!form.student_id || !form.username) return ElMessage.warning('请填写完整信息')
  try {
    // 调用后端核验接口
    await request.post('/auth/users/verify-user/', { 
      student_id: form.student_id, 
      username: form.username 
    })
    activeStep.value = 1
  } catch (err) { /* 拦截器会处理错误提示 */ }
}

// 第二步：提交修改
const submitReset = async () => {
  if (form.new_password !== form.confirm_password) return ElMessage.error('两次密码输入不一致')
  try {
    await request.post('/auth/users/self-reset-password/', form)
    ElMessage.success('密码重置成功，请重新登录')
    router.push('/login')
  } catch (err) {}
}
</script>

<style scoped>
.reset-container {
  height: 100vh; display: flex; justify-content: center; align-items: center;
  background: #f5f7fa;
}
.reset-box { width: 450px; }
</style>