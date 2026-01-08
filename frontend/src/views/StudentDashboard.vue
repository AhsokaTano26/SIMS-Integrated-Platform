<template>
  <div class="common-layout">
    <el-container>
      <el-header class="dashboard-header">
        <div class="logo">🏫 智慧校园学生端</div>
        <div class="user-info">
          <el-tag type="success" effect="plain" class="role-tag">学生</el-tag>
          <span class="username">{{ username }}</span>
          <el-button type="danger" size="small" link @click="handleLogout" style="margin-left: 15px">退出</el-button>
        </div>
      </el-header>

      <el-main class="dashboard-main">
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
                >
                </el-result>

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
                <p v-if="currentCoords" class="coords-tip">
                  经度: {{ currentCoords.lng.toFixed(4) }} | 纬度: {{ currentCoords.lat.toFixed(4) }}
                </p>
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
                <el-table-column prop="reason" label="请假原因" show-overflow-tooltip />
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

    <el-dialog v-model="leaveDialogVisible" title="发起请假申请" width="500px" destroy-on-close>
      <el-form :model="leaveForm" label-width="80px" label-position="left">
        <el-form-item label="请假类型">
          <el-select v-model="leaveForm.type" placeholder="选择请假类型" style="width: 100%">
            <el-option label="病假" value="sick" />
            <el-option label="事假" value="personal" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间区间">
          <el-date-picker
            v-model="leaveForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="请假原因">
          <el-input
            v-model="leaveForm.reason"
            type="textarea"
            rows="3"
            placeholder="请详细说明请假缘由（如：感冒发烧、回家办事等）"
          />
        </el-form-item>

        <el-form-item label="证明材料">
          <el-upload
            action="#"
            list-type="picture-card"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            :on-exceed="handleExceed"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">选填，上传医院假条或相关证明图片</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="leaveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitLeave">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Location, Position, Plus } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const username = ref(JSON.parse(localStorage.getItem('user_info') || '{}').username || '同学')

// --- 状态变量 ---
const locating = ref(false)
const currentCoords = ref(null)
const checkStatus = ref(null)
const leaveList = ref([])
const loadingList = ref(false)
const leaveDialogVisible = ref(false)
const submitting = ref(false)
const uploadFile = ref(null)

const leaveForm = reactive({
  type: 'personal',
  timeRange: [],
  reason: ''
})

// --- 初始化获取数据 ---
const fetchLeaves = async () => {
  loadingList.value = true
  try {
    const data = await request.get('/leaves/')
    leaveList.value = data
  } catch (error) {
    console.error('获取列表失败', error)
  } finally {
    loadingList.value = false
  }
}

onMounted(fetchLeaves)

// --- 打卡逻辑 ---
const startCheckIn = () => {
  locating.value = true
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持定位功能，请在手机端或使用HTTPS访问')
    locating.value = false
    return
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude, longitude } = position.coords
      currentCoords.value = { lat: latitude, lng: longitude }
      try {
        const res = await request.post('/attendance/', {
          lat: latitude,
          lng: longitude
        })
        checkStatus.value = res
        if (res.is_normal) {
          ElMessage.success('打卡成功，位置正常')
        } else {
          ElMessage.warning(`位置异常：距离宿舍 ${res.distance} 米`)
        }
      } catch (err) {
        ElMessage.error('提交打卡失败，请检查网络')
      } finally {
        locating.value = false
      }
    },
    (error) => {
      ElMessage.error('定位失败：无法访问您的位置权限')
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 5000 }
  )
}

// --- 请假申请逻辑 ---
const openLeaveDialog = () => {
  leaveForm.reason = ''
  leaveForm.timeRange = []
  uploadFile.value = null
  leaveDialogVisible.value = true
}

const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一张证明图片')
}

const submitLeave = async () => {
  if (!leaveForm.reason || leaveForm.timeRange.length === 0) {
    return ElMessage.warning('请填写完整的请假时间和原因')
  }

  submitting.value = true
  // 使用 FormData 支持文件上传
  const formData = new FormData()
  formData.append('type', leaveForm.type)
  formData.append('reason', leaveForm.reason)
  formData.append('start_time', leaveForm.timeRange[0].toISOString())
  formData.append('end_time', leaveForm.timeRange[1].toISOString())
  if (uploadFile.value) {
    formData.append('evidence', uploadFile.value)
  }

  try {
    await request.post('/leaves/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('请假申请已提交，请耐心等待审批')
    leaveDialogVisible.value = false
    fetchLeaves() // 刷新列表
  } catch (err) {
    console.error('提交失败', err)
  } finally {
    submitting.value = false
  }
}

// --- 辅助方法 ---
const getStatusTag = (status) => {
  const map = { pending: 'info', approved: 'success', rejected: 'danger', completed: 'warning' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { pending: '待审批', approved: '已准假', rejected: '被驳回', completed: '已销假' }
  return map[status] || status
}

const handleLogout = () => {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.dashboard-header {
  background-color: #409eff;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.logo { font-size: 1.3rem; font-weight: bold; letter-spacing: 1px; }
.user-info { display: flex; align-items: center; }
.role-tag { margin-right: 12px; }
.username { font-size: 14px; font-weight: 500; }

.dashboard-main { background-color: #f0f2f5; min-height: calc(100vh - 60px); padding: 24px; }
.box-card { border-radius: 12px; border: none; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }

.attendance-content { padding: 10px; text-align: center; }
.checkin-empty { padding: 30px 0; color: #909399; font-size: 14px; line-height: 2; }
.coords-tip { margin-top: 15px; font-size: 12px; color: #a8abb2; }

/* 针对移动端的适配 */
@media (max-width: 768px) {
  .el-col { margin-bottom: 20px; }
}
</style>