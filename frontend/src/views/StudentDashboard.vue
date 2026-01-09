<template>
  <div class="common-layout">
    <el-container>
      <el-header class="dashboard-header">
        <div class="logo">🏫 智慧校园学生端</div>
        <div class="user-info">
          <el-tag type="success" effect="plain" class="role-tag">学生</el-tag>
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="el-dropdown-link" style="cursor: pointer; color: white; display: flex; align-items: center;">
              {{ profileForm.username }} <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">👤 个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided style="color: #F56C6C">🚪 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="dashboard-main">
        <div class="user-profile-card">
          <div class="profile-header">
            <div class="avatar-box">
              <el-avatar :size="70" icon="UserFilled" class="custom-avatar" />
            </div>
            <div class="welcome-box">
              <div class="user-title">
                <span class="name">{{ profileForm.username }}！欢迎回来</span>
                <el-tag size="small" effect="dark" class="gender-tag">
                  {{profileForm.gender === 'female' ? '♀ 女' : 
                  (profileForm.gender === 'male' ? '♂ 男' : '⚪ 未知')
                  }}
                </el-tag>
              </div>
              <div class="sub-info">学号：{{ profileForm.student_id }}</div>
            </div>
            <div class="role-badge">学生</div>
          </div>

          <div class="profile-footer">
            <div class="footer-item">
              <el-icon><School /></el-icon> {{ profileForm.college }}学院
            </div>
            <div class="footer-item">
              <el-icon><Reading /></el-icon> 
              专业：{{ profileForm.grade }}{{ profileForm.class_name }} ({{ profileForm.major }})
            </div>
            <div class="footer-item">
              <el-icon><User /></el-icon> 
              辅导员：{{ profileForm.instructor_name || '未指派' }}
            </div>
          </div>
        </div>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="10">
            <el-card class="box-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>📍 定位打卡（晚归/查寝）</span>
                </div>
              </template>
              <div class="attendance-content">
                <el-result
                  v-if="checkStatus"
                  :icon="checkStatus.is_normal ? 'success' : 'warning'"
                  :title="checkStatus.is_normal ? '在位正常' : '位置异常'"
                  :sub-title="checkStatus.msg || `距离目标位置 ${checkStatus.distance} 米`"
                />
                <div v-else class="checkin-empty">
                  <el-icon :size="50" color="#C0C4CC"><Location /></el-icon>
                  <p>系统将校验你当前位置是否在宿舍范围内</p>
                </div>

                <el-button
                  type="primary"
                  size="large"
                  :loading="locating"
                  @click="startCheckIn"
                  style="width: 100%; margin-top: 20px"
                >
                  <el-icon v-if="!locating"><Position /></el-icon>
                  {{ locating ? '正在精准定位...' : '立即打卡' }}
                </el-button>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :sm="14">
            <el-card class="box-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>📝 我的请假记录</span>
                  <el-button type="primary" size="small" plain @click="openLeaveDialog">发起请假</el-button>
                </div>
              </template>
              <el-table :data="leaveList" v-loading="loadingList" stripe style="width: 100%">
                <el-table-column prop="created_at" label="申请日期" width="110">
                  <template #default="scope">
                    {{ new Date(scope.row.created_at).toLocaleDateString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="reason" label="原因" show-overflow-tooltip />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getStatusTag(scope.row.status)">
                      {{ getStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <el-dialog v-model="profileVisible" title="我的个人档案" width="460px" destroy-on-close>
      <el-form :model="profileForm" label-width="100px" label-position="left">
        <el-form-item label="学号">
          <el-input v-model="profileForm.student_id" disabled />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="profileForm.username" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="profileForm.gender">
            <el-radio label="male">男</el-radio>
            <el-radio label="female">女</el-radio>
            <el-radio label="unknown">保密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="profileForm.major" disabled />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="handleUpdateProfile">保存修改</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="leaveDialogVisible" title="发起请假申请" width="500px">
        </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Location, Position, School, Reading, 
  User, ArrowDown, UserFilled 
} from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()

// --- 状态变量 ---
const profileVisible = ref(false)
const updating = ref(false)
const locating = ref(false)
const checkStatus = ref(null)
const leaveList = ref([])
const loadingList = ref(false)
const leaveDialogVisible = ref(false)

// 个人信息数据模型
const profileForm = reactive({
  id: '',
  username: '',
  student_id: '',
  college: '',
  major: '',
  grade: '',
  class_name: '',
  phone: '',
  gender: '',
  instructor_name: '' // 辅导员姓名
})

// --- 初始化逻辑 ---
const loadData = async () => {
  try {
    // 同时获取用户信息和请假列表
    const [userRes, leaveRes] = await Promise.all([
      request.get('/auth/users/me/'),
      request.get('/leaves/')
    ])
    Object.assign(profileForm, userRes)
    leaveList.value = leaveRes
  } catch (err) {
    ElMessage.error('数据加载失败')
  }
}

onMounted(loadData)

// --- 事件处理 ---
const handleCommand = (command) => {
  if (command === 'profile') profileVisible.value = true
  if (command === 'logout') {
    localStorage.clear()
    router.push('/login')
  }
}

const handleUpdateProfile = async () => {
  updating.value = true
  try {
    // 仅 PATCH 允许修改的字段
    await request.patch(`/auth/users/${profileForm.id}/`, {
      username: profileForm.username,
      gender: profileForm.gender,
      phone: profileForm.phone
    })
    ElMessage.success('保存成功')
    profileVisible.value = false
    loadData() // 刷新数据
  } catch (err) {
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

const startCheckIn = () => {
  locating.value = true
  
  // 1. 调用浏览器地理定位 API
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持定位功能')
    locating.value = false
    return
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        // 获取经纬度
        const { latitude, longitude } = position.coords
        
        // 2. 发送 POST 请求到后端 AttendanceView
        // 注意：请确保你的 request.js 中已经配置好了 BaseURL
        const res = await request.post('/attendance/', {
          lat: latitude,
          lng: longitude
        })

        // 3. 将后端返回的 {is_normal, distance, msg} 赋值给响应式变量
        checkStatus.value = res
        
        if (res.is_normal) {
          ElMessage.success('打卡成功：位置正常')
        } else {
          ElMessage.warning(res.msg)
        }
      } catch (err) {
        console.error(err)
        ElMessage.error('打卡失败：' + (err.response?.data?.detail || '服务器异常'))
      } finally {
        locating.value = false
      }
    },
    (error) => {
      locating.value = false
      switch (error.code) {
        case error.PERMISSION_DENIED:
          ElMessage.error("用户拒绝了定位请求，请在浏览器地址栏左侧开启权限")
          break
        case error.POSITION_UNAVAILABLE:
          ElMessage.error("位置信息不可用")
          break
        case error.TIMEOUT:
          ElMessage.error("定位超时，请重试")
          break
        default:
          ElMessage.error("定位发生未知错误")
          break
      }
    },
    {
      enableHighAccuracy: true, // 建议开启高精度，否则经纬度偏差大
      timeout: 10000,
      maximumAge: 0
    }
  )
}
// 辅助函数
const getStatusTag = (s) => s === 'approved' ? 'success' : s === 'rejected' ? 'danger' : 'info'
const getStatusText = (s) => ({ pending: '待审批', approved: '已准假', rejected: '已驳回' }[s] || s)
const openLeaveDialog = () => { leaveDialogVisible.value = true }
</script>

<style scoped>
/* 顶部导航 */
.dashboard-header {
  background-color: #409eff;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

/* 蓝色渐变卡片样式 [关键点] */
.user-profile-card {
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  position: relative;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 8px 20px rgba(24, 144, 255, 0.3);
}

.profile-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.avatar-box {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px;
  border-radius: 50%;
  margin-right: 16px;
}

.user-title .name {
  font-size: 22px;
  font-weight: bold;
  display: block;
  margin-bottom: 8px;
}

.gender-tag {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  margin-left: 8px;
}

.sub-info {
  font-size: 14px;
  opacity: 0.9;
}

.role-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #36cfc9;
  padding: 4px 12px;
  font-size: 12px;
  border-bottom-left-radius: 12px;
}

/* 底部横栏信息 */
.profile-footer {
  display: flex;
  justify-content: space-between;
  background: rgba(0, 0, 0, 0.1);
  margin: 0 -24px -24px -24px;
  padding: 12px 24px;
  font-size: 14px;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dashboard-main { background-color: #f0f2f5; padding: 24px; }
.box-card { border-radius: 12px; margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
.attendance-content { text-align: center; padding: 10px; }
</style>