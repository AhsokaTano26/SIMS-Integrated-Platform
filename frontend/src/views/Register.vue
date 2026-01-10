<template>
  <div class="register-app-container">
    <div class="glass-morph-card">
      <div class="side-brand">
        <div class="brand-content">
          <div class="brand-logo">
            <el-icon :size="40"><Reading /></el-icon>
          </div>
          <h1>立即加入</h1>
          <p>开启您的智能化校园生活助手</p>
          <div class="step-indicator">
            <div :class="['step-dot', { active: true }]"></div>
            <div :class="['step-dot', { active: form.username }]"></div>
            <div :class="['step-dot', { active: form.college }]"></div>
          </div>
        </div>
      </div>

      <div class="form-content">
        <div class="form-header">
          <h2>新用户注册</h2>
          <el-link type="primary" @click="$router.push('/login')" :underline="false">
            已有账号？返回登录
          </el-link>
        </div>

        <el-scrollbar max-height="550px">
          <el-form
            :model="form"
            :rules="rules"
            ref="registerFormRef"
            label-position="top"
            class="styled-form"
          >
            <h3 class="group-title"><el-icon><Lock /></el-icon> 账号安全</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="form.username" placeholder="登录账号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="学号 / 工号" prop="student_id">
                  <el-input v-model="form.student_id" placeholder="ID编号" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="设置密码" prop="password">
                  <el-input v-model="form.password" type="password" show-password />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="确认密码" prop="re_password">
                  <el-input v-model="form.re_password" type="password" show-password />
                </el-form-item>
              </el-col>
            </el-row>

            <h3 class="group-title"><el-icon><User /></el-icon> 个人资料</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="手机号码" prop="phone">
                  <el-input v-model="form.phone" placeholder="11位手机号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="性别" prop="gender">
                  <el-radio-group v-model="form.gender">
                    <el-radio label="男">男</el-radio>
                    <el-radio label="女">女</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="注册身份" prop="role">
              <el-segmented v-model="form.role" :options="roleOptions" class="custom-segmented" />
            </el-form-item>

            <h3 class="group-title"><el-icon><School /></el-icon> 教育/办公信息</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="所属学院" prop="college">
                  <el-input v-model="form.college" placeholder="学院全称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="当前年级" prop="grade">
                  <el-input v-model="form.grade" placeholder="例：2023级" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="专业名称" prop="major">
                  <el-input v-model="form.major" />
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="form.role === 'student'">
                <el-form-item label="班级" prop="class_name">
                  <el-input v-model="form.class_name" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="培养层次" prop="education_level">
              <el-select v-model="form.education_level" style="width: 100%">
                <el-option label="本科生" value="undergraduate" />
                <el-option label="硕士研究生" value="postgraduate" />
                <el-option label="博士研究生" value="doctoral" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-scrollbar>

        <div class="footer-actions">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="reg-submit-btn"
            @click="handleRegister"
          >
            完成注册，进入系统
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Reading, User, Lock, School } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const registerFormRef = ref(null)
const loading = ref(false)

const roleOptions = [
  { label: '学生', value: 'student' },
  { label: '辅导员', value: 'teacher' }
]

const form = reactive({
  username: '', password: '', re_password: '', role: 'student',
  student_id: '', college: '', major: '', grade: '',
  class_name: '', education_level: 'undergraduate', gender: '男', phone: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const rules = computed(() => ({
  username: [{ required: true, message: '必填', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '最少6位', trigger: 'blur' }],
  re_password: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }],
  student_id: [{ required: true, message: '必填', trigger: 'blur' }],
  phone: [{ required: true, pattern: /^1[3-9]\d{9}$/, message: '格式错误', trigger: 'blur' }],
  college: [{ required: true, message: '必填', trigger: 'blur' }]
}))

const handleRegister = async () => {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const { re_password, ...submitData } = form
        await request.post('/auth/users/', submitData)
        ElMessage.success('注册成功！')
        router.push('/login')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-app-container {
  height: 100vh;
  background: #f0f4f8;
  background-image: radial-gradient(at 0% 0%, rgba(64, 158, 255, 0.15) 0, transparent 50%),
                    radial-gradient(at 100% 100%, rgba(103, 194, 58, 0.1) 0, transparent 50%),
                      url('/login-bg.jpg');
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.glass-morph-card {
  width: 900px;
  height: 700px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  display: flex;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* 左侧品牌区 */
.side-brand {
  width: 35%;
  background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%);
  padding: 40px;
  color: white;
  display: flex;
  align-items: center;
  position: relative;
}

.side-brand::before {
  content: "";
  position: absolute;
  top: -20%; left: -20%;
  width: 150px; height: 150px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

.brand-logo {
  width: 80px; height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 30px;
}

.side-brand h1 { font-size: 28px; margin-bottom: 15px; font-weight: 700; }
.side-brand p { font-size: 14px; opacity: 0.8; line-height: 1.6; }

.step-indicator {
  margin-top: 50px;
  display: flex;
  gap: 10px;
}
.step-dot {
  width: 30px; height: 4px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  transition: 0.3s;
}
.step-dot.active { background: white; width: 50px; }

/* 右侧表单区 */
.form-content {
  flex: 1;
  padding: 40px 50px;
  display: flex;
  flex-direction: column;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.custom-segmented {
  /* 移除 block 后，通过 min-width 保证点击区域够大 */
  --el-segmented-item-selected-color: #409eff;
}

:deep(.el-segmented__item) {
  min-width: 100px; /* 确保长文字也能完整显示 */
  padding: 0 15px;  /* 增加左右内距 */
}

/* 解决文字被截断的核心样式 */
:deep(.el-segmented__item-label) {
  white-space: nowrap !important; /* 强制文字不换行 */
  overflow: visible !important;   /* 允许内容撑开 */
}
/* 1. 确保文字在滑块上方显示，并强制文字不换行 */
:deep(.el-segmented__item-label) {
  position: relative;
  z-index: 2; /* 提升文字层级，确保在蓝色滑块上方 */
  display: flex;
  justify-content: center;
  align-items: center;
  white-space: nowrap !important; /* 严禁换行 */
  color: inherit; /* 继承父级颜色 */
}

/* 2. 优化滑块层级 */
:deep(.el-segmented__item-selected) {
  z-index: 1; /* 滑块层级设为 1 */
}

/* 3. 解决选中状态下的文字颜色反馈 */
:deep(.el-segmented__item.is-selected .el-segmented__item-label) {
  color: #ffffff !important; /* 选中时文字强制设为白色 */
  font-weight: 600;
}

/* 4. 如果使用了 block 属性，增加内部左右间距，防止文字紧贴边缘 */
:deep(.el-segmented__item) {
  padding: 0 12px !important;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
}
.form-header h2 { font-size: 22px; color: #1f2f3d; }

.group-title {
  font-size: 14px;
  color: #409EFF;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 25px 0 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f2f5;
}

/* 表单控件优化 */
:deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 4px !important;
}

:deep(.el-input__wrapper) {
  box-shadow: none !important;
  background-color: #f5f7fa;
  border: 1px solid transparent;
  transition: all 0.3s;
  padding: 5px 12px;
}

:deep(.el-input__wrapper:hover) {
  background-color: #edf2f7;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #fff;
  border-color: #409EFF;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1) !important;
}

.footer-actions {
  margin-top: auto;
  padding-top: 20px;
}

.custom-segmented :deep(.el-segmented__item) {
  min-width: 120px;
}

.reg-submit-btn {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border: none;
}

.reg-submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(64, 158, 255, 0.2);
}

/* 隐藏滚动条但保留功能 */
:deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}
</style>