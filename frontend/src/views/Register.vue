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
                  <el-input v-model="form.username" placeholder="用户姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="学号 / 工号" prop="student_id">
                  <el-input v-model="form.student_id" placeholder="用户账号" />
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
                    <el-radio label="male">男</el-radio>
                    <el-radio label="female">女</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="注册身份" prop="role">
              <el-segmented v-model="form.role" :options="roleOptions" class="custom-segmented" />
            </el-form-item>

            <template v-if="form.role === 'student'">
              <h3 class="group-title"><el-icon><Location /></el-icon> 住宿信息</h3>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="住宿类型" prop="dorm_type">
                    <el-select v-model="form.dorm_type" style="width: 100%">
                      <el-option label="校内住宿" value="internal" />
                      <el-option label="校外住宿" value="external" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12" v-if="form.dorm_type === 'internal'">
                  <el-form-item label="所属宿舍楼" prop="dormitory">
                    <el-select v-model="form.dormitory" placeholder="选择楼栋" style="width: 100%">
                      <el-option
                        v-for="item in dormList"
                        :key="item.id"
                        :label="item.name"
                        :value="item.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item 
                :label="form.dorm_type === 'internal' ? '寝室号' : '详细住址'" 
                prop="address"
              >
                <el-input 
                  v-model="form.address" 
                  :placeholder="form.dorm_type === 'internal' ? '例：302' : '请输入详细的校外居住地址'" 
                />
              </el-form-item>
            </template>            

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
                <el-form-item :label="form.role === 'teacher' ? '所属部门' : '专业名称'" prop="major">
                  <el-input v-model="form.major" />
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="form.role === 'student'">
                <el-form-item label="班级" prop="class_name">
                  <el-input v-model="form.class_name" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item :label="form.role === 'teacher' ? '学历' : '培养层次'" prop="education_level">
              <el-select v-model="form.education_level" style="width: 100%">
                <el-option label="本科生" value="undergraduate" />
                <el-option label="硕士研究生" value="master" />
                <el-option label="博士研究生" value="doctor" />
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
import { reactive, ref, computed,onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Reading, User, Lock, School,Location } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const registerFormRef = ref(null)
const loading = ref(false)
const dormList = ref([]) // 存储宿舍楼列表

const roleOptions = [
  { label: '学生', value: 'student' },
  { label: '辅导员', value: 'teacher' }
]

const form = reactive({
  username: '', password: '', re_password: '', role: 'student',
  student_id: '', college: '', major: '', grade: '',
  class_name: '', education_level: 'undergraduate', gender: 'male', phone: '',
  dorm_type: 'internal',
  dormitory: null,
  address: ''
})
const fetchDormList = async () => {
  try {
    const res = await request.get('/auth/users/dormitories/') 
    
    // 关键修复：直接打印 res 看看是不是数组
    console.log('拦截器处理后的原始 res:', res) 
    
    // 兼容性写法：如果 res 是数组直接用，否则用 res.data
    dormList.value = Array.isArray(res) ? res : res.data
    
    console.log('最终赋值给 dormList 的内容:', dormList.value)
  } catch (error) {
    console.error('获取宿舍列表失败', error)
  }
}

onMounted(() => {
  fetchDormList()
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
  college: [{ required: true, message: '必填', trigger: 'blur' }],
  // 新增：年级必填
  grade: [{ required: true, message: '请输入当前年级', trigger: 'blur' }],
  
  // 新增：专业/部门必填 (Label 会随角色变，但 key 都是 major)
  major: [{ 
    required: true, 
    message: form.role === 'teacher' ? '请输入所属部门' : '请输入专业名称',
    trigger: 'blur' 
  }],
  
  // 新增：学生身份时班级必填
  class_name: [{ 
    required: form.role === 'student', 
    message: '请输入班级名称', 
    trigger: 'blur' 
  }],
  // 住宿校验逻辑
  dorm_type: [{ required: form.role === 'student' && form.dorm_type === 'internal', message: '请选择住宿类型', trigger: 'change' }],
  dormitory: [{ 
    required: form.role === 'student' && form.dorm_type === 'internal', 
    message: '请选择宿舍楼', 
    trigger: 'change' 
  }],
  address: [{ 
    required: form.role === 'student', 
    message: '该项为必填项', 
    trigger: 'blur' 
  }]
}))

const handleRegister = async () => {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const { re_password, ...submitData } = form
        await request.post('/auth/users/', submitData)
        ElMessage.success('注册成功！您的登录账号为：' + form.student_id)
        router.push('/login')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
/* 1. 基础容器与背景 */
.register-app-container {
  height: 100vh;
  background: #f0f4f8;
  background-image: 
    radial-gradient(at 0% 0%, rgba(64, 158, 255, 0.15) 0, transparent 50%),
    radial-gradient(at 100% 100%, rgba(103, 194, 58, 0.1) 0, transparent 50%),
    url('/login-bg.jpg');
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

/* 2. 玻璃态卡片主体 */
.glass-morph-card {
  width: 900px;
  height: 700px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px); /* 兼容 Safari */
  border-radius: 24px;
  display: flex;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* 3. 左侧品牌区 */
.side-brand {
  width: 35%;
  background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); /* 渐变色稍作微调更显现代 */
  padding: 40px;
  color: white;
  display: flex;
  flex-direction: column; /* 修正：垂直排列 */
  justify-content: center;
  position: relative;
}

.side-brand::before {
  content: "";
  position: absolute;
  top: -10%; left: -10%;
  width: 200px; height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.brand-logo {
  width: 64px; height: 64px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24px;
  font-size: 32px;
}

.side-brand h1 { font-size: 26px; margin-bottom: 12px; font-weight: 700; }
.side-brand p { font-size: 14px; opacity: 0.9; line-height: 1.6; }

.step-indicator {
  margin-top: 40px;
  display: flex;
  gap: 8px;
}
.step-dot {
  width: 20px; height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  transition: all 0.4s ease;
}
.step-dot.active { background: white; width: 40px; }

/* 4. 右侧表单区布局 */
.form-content {
  flex: 1;
  padding: 40px 60px;
  display: flex;
  flex-direction: column;
  background: white; /* 增强表单清晰度 */
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}
.form-header h2 { font-size: 24px; color: #1f2f3d; margin: 0; }

/* 5. 分段控制器 (Student/Teacher 选择) 深度优化 */
.custom-segmented {
  --el-segmented-item-selected-bg-color: #409eff;
}

:deep(.el-segmented) {
  padding: 4px;
  border-radius: 8px;
  background: #f4f4f5;
}

:deep(.el-segmented__item) {
  min-width: 100px;
  padding: 0 16px !important;
  transition: all 0.3s;
}

:deep(.el-segmented__item-label) {
  display: flex;
  justify-content: center;
  align-items: center;
  white-space: nowrap !important;
  font-size: 14px;
  z-index: 2; /* 确保文字在蓝色背景滑块之上 */
  position: relative;
}

/* 选中状态文字变为白色 */
:deep(.el-segmented__item.is-selected .el-segmented__item-label) {
  color: #ffffff !important;
  font-weight: 600;
}

/* 6. 表单细节优化 */
.group-title {
  font-size: 14px;
  color: #409eff;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 20px 0 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f2f5;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  padding-bottom: 4px !important;
}

:deep(.el-input__wrapper) {
  box-shadow: none !important;
  background-color: #f5f7fa;
  border: 1px solid transparent;
  padding: 8px 12px;
  border-radius: 10px;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #fff;
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1) !important;
}

/* 7. 提交按钮 */
.footer-actions {
  margin-top: auto;
  padding-top: 20px;
}

.reg-submit-btn {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(90deg, #409eff, #3b82f6);
  border: none;
  transition: all 0.3s;
}

.reg-submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.3);
}

/* 8. 滚动条美化 (针对超长表单) */
:deep(.el-scrollbar__bar.is-vertical) {
  width: 4px;
}
</style>