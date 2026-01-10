<template>
  <div class="profile-container">
    <el-page-header @back="goBack" title="返回首页" class="page-header">
      <template #content>
        <span class="header-title"> 👤 个人档案中心 </span>
      </template>
    </el-page-header>

    <div class="profile-content">
      <el-row :gutter="20">
        <el-col :md="8" :xs="24">
          <el-card shadow="hover" class="profile-aside-card">
            <div class="avatar-section">
              <el-avatar 
                :size="120" 
                :src="getFullAvatarUrl(profileForm.avatar_url)" 
                class="avatar-hover"
                @click="triggerUpload"
              >
                <el-icon :size="60"><UserFilled /></el-icon>
              </el-avatar>
              <input type="file" ref="fileInput" style="display: none" accept="image/*" @change="handleFileChange" />
              <h3>{{ profileForm.username }}</h3>
              <el-tag effect="dark" round>{{ profileForm.role === 'student' ? '正式学生' : '辅导员' }}</el-tag>
            </div>
            
            <el-divider />
            
            <div class="basic-list">
              <div class="item">
                <span class="label">学号</span>
                <span class="value">{{ profileForm.student_id }}</span>
              </div>
              <div class="item">
                <span class="label">手机号</span>
                <span class="value">{{ profileForm.phone || '未填写' }}</span>
              </div>
              <div class="item">
                <span class="label">性别</span>
                <span class="value">{{ translateGender(profileForm.gender) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :md="16" :xs="24">
          <el-card shadow="hover" class="detail-card">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="基本资料" name="info">
                <el-descriptions title="基础信息" :column="2" border class="mt-4">
                  <el-descriptions-item label="真实姓名">{{ profileForm.username }}</el-descriptions-item>
                  <el-descriptions-item label="账号状态">
                    <el-badge is-dot type="success"> 正常使用中 </el-badge>
                  </el-descriptions-item>
                  <el-descriptions-item label="联系电话">{{ profileForm.phone || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="注册时间">{{ formatDate(profileForm.date_joined) }}</el-descriptions-item>
                </el-descriptions>

                <el-descriptions title="教育/办公信息" :column="2" border class="mt-6">
                  <el-descriptions-item label="所属学院">{{ profileForm.college }}</el-descriptions-item>
                  <el-descriptions-item label="当前年级">{{ profileForm.grade }}级</el-descriptions-item>
                  <el-descriptions-item label="专业名称">{{ profileForm.major }}</el-descriptions-item>
                  <el-descriptions-item label="班级">{{ profileForm.class_name }}</el-descriptions-item>
                  <el-descriptions-item label="辅导员">{{ profileForm.instructor_name || '未分配' }}</el-descriptions-item>
                </el-descriptions>

                <el-descriptions title="住宿信息" :column="2" border class="mt-6">
                  <el-descriptions-item label="住宿类型">
                    <el-tag size="small">{{ profileForm.stay_type === 'on_campus' ? '校内住宿' : '校外住宿' }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="宿舍楼">{{ profileForm.dormitory_name || '5号楼' }}</el-descriptions-item>
                  <el-descriptions-item label="寝室号">{{ profileForm.room_number || '583' }}</el-descriptions-item>
                </el-descriptions>

                <div class="form-actions">
                  <el-button type="primary" icon="Edit" @click="handleEdit">编辑个人资料</el-button>
                </div>
              </el-tab-pane>

              <el-tab-pane label="账号安全" name="security">
                <div class="security-item">
                  <div class="info">
                    <div class="title">登录密码</div>
                    <div class="desc">安全性高的密码由字母、数字和符号组成</div>
                  </div>
                  <el-button link type="primary">修改密码</el-button>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled, Edit } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const activeTab = ref('info')
const fileInput = ref(null)

const profileForm = reactive({
  id: '', username: '', student_id: '', college: '', major: '',
  grade: '', class_name: '', phone: '', gender: '', instructor_name: '',
  avatar_url: '', stay_type: '', dormitory_name: '', room_number: '',
  date_joined: ''
})

const loadProfile = async () => {
  try {
    const res = await request.get('/auth/users/me/')
    Object.assign(profileForm, res)
  } catch (err) {
    ElMessage.error('获取个人档案失败')
  }
}

onMounted(loadProfile)

const goBack = () => router.push('/dashboard')
const translateGender = (g) => ({ male: '男', female: '女', unknown: '保密' }[g] || '保密')
const formatDate = (d) => d ? new Date(d).toLocaleDateString() : '-'
const getFullAvatarUrl = (url) => url ? `http://127.0.0.1:8000${url}?t=${Date.now()}` : ''

const triggerUpload = () => fileInput.value.click()

const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('avatar', file)
  try {
    await request.patch(`/auth/users/${profileForm.id}/`, formData)
    ElMessage.success('头像更新成功')
    loadProfile()
  } catch (e) { ElMessage.error('上传失败') }
}

const handleEdit = () => {
  ElMessage.info('正在进入编辑模式...')
  // 此处可跳转到编辑页或打开 Dialog
}
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}
.page-header {
  background: #fff;
  padding: 15px 24px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
}
.header-title { font-weight: bold; font-size: 18px; }
.avatar-section {
  text-align: center;
  padding: 20px 0;
}
.avatar-hover {
  cursor: pointer;
  border: 4px solid #f0f2f5;
  transition: transform 0.3s;
}
.avatar-hover:hover { transform: scale(1.05); }
.basic-list {
  padding: 10px 0;
}
.basic-list .item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 14px;
}
.basic-list .label { color: #909399; }
.basic-list .value { color: #303133; font-weight: 500; }
.detail-card { min-height: 600px; }
.mt-4 { margin-top: 1rem; }
.mt-6 { margin-top: 2rem; }
.form-actions { margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }
.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid #f0f2f5;
}
.security-item .title { font-size: 16px; font-weight: bold; }
.security-item .desc { font-size: 13px; color: #909399; }
</style>