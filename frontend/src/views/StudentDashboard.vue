<template>
  <div class="common-layout">
    <el-container>
      <el-header class="dashboard-header">
        <div class="logo">🏫 <span class="brand">智慧校园</span>学生端</div>
        <div class="user-info">
          <span class="welcome-text">欢迎回来,</span>
          <span class="username">{{ userInfo.username }}</span>
          <el-divider direction="vertical" />
          <el-button type="danger" size="small" link @click="handleLogout">退出系统</el-button>
        </div>
      </el-header>

      <el-main class="dashboard-main">
        <el-row :gutter="20" class="margin-bottom-20">
          <el-col :span="24">
            <el-card shadow="never" class="profile-summary-card">
              <div class="profile-flex-container">
                <div class="user-avatar-section">
                  <el-avatar :size="64" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
                  <div class="user-basic-info">
                    <h3>{{ userInfo.username }} <el-tag size="small" effect="dark">{{ userInfo.education_level || '本科生' }}</el-tag></h3>
                    <p class="sub-text">{{ userInfo.college }} · {{ userInfo.major }} · {{ userInfo.class_name }}</p>
                    <p class="id-text">学号: {{ userInfo.student_id }}</p>
                  </div>
                </div>
                <div class="stat-group">
                  <div class="stat-item">
                    <span class="stat-label">本月打卡</span>
                    <span class="stat-value">28<small>/31</small></span>
                  </div>
                  <el-divider direction="vertical" class="stat-divider" />
                  <div class="stat-item">
                    <span class="stat-label">待处理请假</span>
                    <span class="stat-value warning">{{ pendingLeaveCount }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="10">
            <el-card class="box-card action-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>📍 定位打卡</span>
                  <el-tag size="small" type="info">晚归/查寝</el-tag>
                </div>
              </template>
              <div class="attendance-content">
                <el-result
                  v-if="checkStatus"
                  :icon="checkStatus.is_normal ? 'success' : 'warning'"
                  :title="checkStatus.is_normal ? '在位正常' : '位置异常'"
                  :sub-title="checkStatus.msg || `距离目标位置 ${checkStatus.distance} 米`"
                >
                </el-result>

                <div v-else class="checkin-empty">
                  <div class="empty-icon-bg">
                    <el-icon :size="40" color="#409EFF"><Location /></el-icon>
                  </div>
                  <p>系统将校验你当前位置是否在宿舍范围内</p>
                </div>

                <el-button
                  type="primary"
                  size="large"
                  round
                  :loading="locating"
                  @click="startCheckIn"
                  class="full-width-btn"
                >
                  <el-icon v-if="!locating" style="margin-right: 8px"><Position /></el-icon>
                  {{ locating ? '正在精准定位...' : '立即提交打卡' }}
                </el-button>
                <p v-if="currentCoords" class="coords-tip">
                  最后定位：{{ currentCoords.lng.toFixed(4) }}, {{ currentCoords.lat.toFixed(4) }}
                </p>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :sm="14">
            <el-card class="box-card table-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>📝 我的请假记录</span>
                  <el-button type="primary" size="small" icon="Plus" @click="openLeaveDialog">发起请假</el-button>
                </div>
              </template>
              <el-table :data="leaveList" v-loading="loadingList" stripe height="320px">
                <el-table-column prop="created_at" label="申请日期" width="120">
                  <template #default="scope">
                    {{ new Date(scope.row.created_at).toLocaleDateString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="reason" label="原因" show-overflow-tooltip />
                <el-table-column prop="status" label="状态" width="100" align="right">
                  <template #default="scope">
                    <el-tag :type="getStatusTag(scope.row.status)" effect="light">
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

    <el-dialog v-model="leaveDialogVisible" title="发起请假申请" width="500px" destroy-on-close align-center>
      <el-form :model="leaveForm" label-width="80px">
        <el-form-item label="请假类型">
          <el-radio-group v-model="leaveForm.type">
            <el-radio-button label="sick">病假</el-radio-button>
            <el-radio-button label="personal">事假</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="时间区间">
          <el-date-picker
            v-model="leaveForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="请假原因">
          <el-input v-model="leaveForm.reason" type="textarea" rows="3" placeholder="详细说明缘由..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="leaveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitLeave">确认提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, Position } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()

// 从本地存储获取所有字段
const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))

const pendingLeaveCount = computed(() => {
  return leaveList.value.filter(item => item.status === 'pending').length
})

// --- 其余 Logic 部分与原代码一致，只需确保 request 的路径正确 ---
const locating = ref(false)
const currentCoords = ref(null)
const checkStatus = ref(null)
const leaveList = ref([])
const loadingList = ref(false)
const leaveDialogVisible = ref(false)
const submitting = ref(false)

const leaveForm = reactive({
  type: 'personal',
  timeRange: [],
  reason: ''
})

const fetchLeaves = async () => {
  loadingList.value = true
  try {
    const data = await request.get('/leaves/')
    leaveList.value = data
  } catch (error) {
    console.error('Fetch failed', error)
  } finally {
    loadingList.value = false
  }
}

onMounted(fetchLeaves)

const startCheckIn = () => {
  locating.value = true
  if (!navigator.geolocation) {
    ElMessage.error('环境不支持定位')
    locating.value = false
    return
  }
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude, longitude } = position.coords
      currentCoords.value = { lat: latitude, lng: longitude }
      try {
        const res = await request.post('/attendance/', { lat: latitude, lng: longitude })
        checkStatus.value = res
      } catch (err) {
        ElMessage.error('提交失败')
      } finally {
        locating.value = false
      }
    },
    () => {
      ElMessage.error('定位失败，请检查权限')
      locating.value = false
    }
  )
}

const openLeaveDialog = () => {
  leaveDialogVisible.value = true
}

const submitLeave = async () => {
  submitting.value = true
  try {
    const postData = {
      type: leaveForm.type,
      reason: leaveForm.reason,
      start_time: leaveForm.timeRange[0].toISOString(),
      end_time: leaveForm.timeRange[1].toISOString()
    }
    await request.post('/leaves/', postData)
    ElMessage.success('提交成功')
    leaveDialogVisible.value = false
    fetchLeaves()
  } finally {
    submitting.value = false
  }
}

const getStatusTag = (s) => ({ pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info')
const getStatusText = (s) => ({ pending: '待审批', approved: '已通过', rejected: '被驳回', completed: '已销假' }[s] || s)

const handleLogout = () => {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
/* 核心视觉升级 */
.dashboard-header {
  background-color: #ffffff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}
.logo { font-size: 1.2rem; font-weight: 600; color: #303133; }
.brand { color: #409EFF; margin-right: 4px; }
.welcome-text { color: #909399; font-size: 13px; margin-right: 8px; }
.username { font-weight: 600; color: #303133; }

.dashboard-main {
  background-color: #f8fafc;
  min-height: calc(100vh - 60px);
  padding: 30px 40px;
}

/* 档案卡片样式 */
.profile-summary-card {
  border-radius: 16px;
  border: none;
  background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
}
.profile-flex-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.user-avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
}
.user-basic-info h3 { margin: 0 0 5px 0; font-size: 22px; }
.sub-text { margin: 0; color: #606266; font-size: 14px; }
.id-text { margin: 4px 0 0 0; color: #909399; font-size: 12px; }

.stat-group {
  display: flex;
  align-items: center;
  gap: 30px;
}
.stat-item { text-align: center; }
.stat-label { display: block; font-size: 13px; color: #909399; margin-bottom: 5px; }
.stat-value { font-size: 24px; font-weight: bold; color: #303133; }
.stat-value.warning { color: #E6A23C; }
.stat-divider { height: 40px; border-left: 1px solid #dcdfe6; }

/* 业务卡片通用 */
.box-card {
  border-radius: 16px;
  border: none;
  min-height: 400px;
}
.margin-bottom-20 { margin-bottom: 20px; }
.full-width-btn { width: 100%; margin-top: 20px; padding: 25px; font-size: 16px; }

/* 打卡内容美化 */
.empty-icon-bg {
  width: 80px;
  height: 80px;
  background-color: #ecf5ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}
.checkin-empty p { color: #909399; font-size: 14px; }
.coords-tip { margin-top: 15px; font-size: 12px; color: #c0c4cc; }

@media (max-width: 768px) {
  .dashboard-main { padding: 15px; }
  .profile-flex-container { flex-direction: column; align-items: flex-start; gap: 20px; }
  .stat-group { width: 100%; justify-content: space-around; }
}
</style>