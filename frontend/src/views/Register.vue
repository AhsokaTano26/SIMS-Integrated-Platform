<template>
  <div class="register-container">
    <el-card class="register-box" shadow="always">
      <template #header>
        <div class="card-header">
          <b style="font-size: 1.2rem">新用户注册</b>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="registerFormRef" label-width="80px" label-position="top">

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="登录账号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学号/工号" prop="student_id">
              <el-input v-model="form.student_id" placeholder="唯一编号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设置密码" prop="password">
              <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="re_password">
              <el-input v-model="form.re_password" type="password" show-password placeholder="请再次输入密码" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="11位手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="选择性别" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="身份角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio label="student">学生</el-radio>
            <el-radio label="teacher">辅导员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider content-position="left">组织与教务信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学院" prop="college">
              <el-input v-model="form.college" placeholder="如：计算机学院" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年级" prop="grade">
              <el-input v-model="form.grade" placeholder="如：2023级" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="专业" prop="major">
              <el-input v-model="form.major" placeholder="如：软件工程" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级" prop="class_name">
              <el-input v-model="form.class_name" placeholder="如：01班" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="培养层次/学历" prop="education_level">
          <el-select v-model="form.education_level" placeholder="选择培养层次" style="width: 100%">
            <el-option label="本科生" value="undergraduate" />
            <el-option label="硕士研究生" value="postgraduate" />
            <el-option label="博士研究生" value="doctoral" />
          </el-select>
        </el-form-item>

        <div class="action-area">
          <el-button
            type="primary"
            :loading="loading"
            @click="handleRegister"
            size="large"
            class="submit-btn"
          >
            {{ loading ? '正在提交注册...' : '立即注册' }}
          </el-button>
          <el-button link @click="$router.push('/login')" :disabled="loading">
            已有账号？去登录
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref,computed } from 'vue'
import request from '../utils/request'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const registerFormRef = ref(null)
const loading = ref(false) // 控制按钮加载状态

const form = reactive({
  username: '',
  password: '',
  re_password: '', // 前端校验用字段
  role: 'student',
  student_id: '',
  college: '',
  major: '',
  grade: '',
  class_name: '',
  education_level: 'undergraduate',
  gender: '',
  phone: ''
})

// 自定义规则：校验两次密码是否一致
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = computed(() => {
  const isStudent = form.role === 'student'
  const isTeacher = form.role === 'teacher'

  // 基础公共规则
  const baseRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
    ],
    re_password: [
      { required: true, validator: validateConfirmPassword, trigger: 'blur' }
    ],
    student_id: [{ required: true, message: '请输入学号/工号', trigger: 'blur' }],
    phone: [
      { required: true, message: '请输入手机号', trigger: 'blur' },
      { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的11位手机号', trigger: 'blur' }
    ],
    gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
    // 学院在两种角色下都是必填
    college: [{ required: true, message: '请输入学院', trigger: 'blur' }],
    // 年级在两种角色下都是必填
    grade: [{ required: true, message: '请输入年级', trigger: 'blur' }],
    // 专业在两种角色下都是必填
    major: [{ required: true, message: '请输入专业', trigger: 'blur' }],
    // 培养层次/学历在两种角色下都是必填
    education_level: [{ required: true, message: '请选择培养层次/学历', trigger: 'change' }]
  }

  // 3. 只有学生身份时，班级才是必填
  if (isStudent) {
    baseRules.class_name = [{ required: true, message: '请输入班级', trigger: 'blur' }]
  }

  return baseRules
})

const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true // 开启加载状态
      try {
        // 解构赋值：剔除 re_password，只发送后端需要的字段
        const { re_password, ...submitData } = form
        await request.post('/auth/users/', submitData)

        ElMessage.success('注册成功，欢迎加入！')
        router.push('/login')
      } catch (err) {
        console.error('注册错误:', err)
        // 错误提示通常由 request.js 拦截器统一处理，此处无需重复
      } finally {
        loading.value = false // 无论成功失败都关闭加载状态
      }
    } else {
      ElMessage.warning('请完善表单信息后再试')
    }
  })
}
</script>

<style scoped>
.register-container {
  background: #f5f7fa;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('/login-bg.jpg');
  background-size: cover;
  background-position: center;
}

.register-box {
  width: 100%;
  max-width: 600px;
  border-radius: 15px;
  background-color: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border: none;
}

.action-area {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.submit-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  letter-spacing: 2px;
  transition: all 0.3s;
}

/* 覆盖 Element Plus 样式 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #444;
  padding-bottom: 4px !important;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset !important;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}
</style>