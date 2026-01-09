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
                  <el-button type="primary" size="small" icon="Plus" @click="openLeaveDialog">发起请假</el-button>
                </div>
              </template>

              <el-table :data="leaveList" v-loading="loadingList" stripe style="width: 100%">
                <el-table-column prop="reason" label="事由" show-overflow-tooltip min-width="100" />

                <el-table-column label="起止时间" width="180">
                  <template #default="scope">
                    <div style="font-size: 12px; color: #666;">
                      {{ formatDate(scope.row.start_time) }}<br/>
                      {{ formatDate(scope.row.end_time) }}
                    </div>
                  </template>
                </el-table-column>

                <el-table-column label="状态" width="90">
                  <template #default="scope">
                    <el-tag :type="getStatusTag(scope.row.status)" size="small">
                      {{ getStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column label="老师意见" show-overflow-tooltip>
                  <template #default="scope">
                    <span style="font-size: 12px; color: #909399">{{ scope.row.comment || '-' }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="操作" width="100" fixed="right">
                  <template #default="scope">
                    <el-button
                      v-if="scope.row.status === 'approved' && !scope.row.report_back_time"
                      type="success" size="small" link
                      @click="handleReportBack(scope.row)"
                    >
                      销假
                    </el-button>
                    <el-button
                      v-else-if="scope.row.status === 'returned'"
                      type="warning" size="small" link
                      @click="handleEdit(scope.row)"
                    >
                      修改
                    </el-button>
                    <span v-else-if="scope.row.report_back_time" style="color: #67C23A; font-size: 12px;">
                      已返校
                    </span>
                    <span v-else>-</span>
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
        <el-form-item label="学号"><el-input v-model="profileForm.student_id" disabled /></el-form-item>
        <el-form-item label="真实姓名"><el-input v-model="profileForm.username" /></el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="profileForm.gender">
            <el-radio label="male">男</el-radio>
            <el-radio label="female">女</el-radio>
            <el-radio label="unknown">保密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="专业"><el-input v-model="profileForm.major" disabled /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="profileForm.phone" placeholder="请输入手机号" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="handleUpdateProfile">保存修改</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="leaveDialogVisible"
      :title="isEditMode ? '修改申请' : '发起请假申请'"
      width="500px"
    >
      <el-form :model="leaveForm" :rules="leaveRules" ref="leaveFormRef" label-width="80px">
        <el-form-item label="请假事由" prop="reason">
          <el-input
            v-model="leaveForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请详细说明请假原因..."
          />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="leaveForm.start_time"
            type="datetime"
            placeholder="选择离校时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="预计返回" prop="end_time">
          <el-date-picker
            v-model="leaveForm.end_time"
            type="datetime"
            placeholder="选择返校时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="leaveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitLeave">
          {{ isEditMode ? '重新提交' : '提交申请' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Location, Position, School, Reading,
  User, ArrowDown, UserFilled, Plus
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

// 请假相关状态
const leaveDialogVisible = ref(false)
const submitting = ref(false)
const leaveFormRef = ref(null)
const isEditMode = ref(false)
const currentLeaveId = ref(null)

const leaveForm = reactive({
  reason: '',
  start_time: '',
  end_time: ''
})

const leaveRules = {
  reason: [{ required: true, message: '请输入请假事由', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

// 个人信息数据模型
const profileForm = reactive({
  id: '', username: '', student_id: '',
  college: '', major: '', grade: '',
  class_name: '', phone: '', gender: '',
  instructor_name: ''
})

// --- 初始化逻辑 ---
const loadData = async () => {
  try {
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

// --- 事件处理：通用 ---
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
    await request.patch(`/auth/users/${profileForm.id}/`, {
      username: profileForm.username,
      gender: profileForm.gender,
      phone: profileForm.phone
    })
    ElMessage.success('保存成功')
    profileVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

const startCheckIn = () => {
  locating.value = true
  setTimeout(() => { locating.value = false }, 2000)
}

// --- 事件处理：请假核心逻辑 ---

// 打开新增弹窗
const openLeaveDialog = () => {
  isEditMode.value = false
  leaveForm.reason = ''
  leaveForm.start_time = ''
  leaveForm.end_time = ''
  leaveDialogVisible.value = true
}

// 处理退回修改
const handleEdit = (row) => {
  isEditMode.value = true
  currentLeaveId.value = row.id
  leaveForm.reason = row.reason
  leaveForm.start_time = row.start_time
  leaveForm.end_time = row.end_time
  leaveDialogVisible.value = true
}

// 提交请假（新增或修改）
const handleSubmitLeave = async () => {
  if (!leaveFormRef.value) return
  await leaveFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEditMode.value) {
          // 修改逻辑：修改内容并将状态重置为 pending (后端逻辑决定)
          await request.put(`/leaves/${currentLeaveId.value}/`, { ...leaveForm, status: 'pending' })
          ElMessage.success('已重新提交申请')
        } else {
          // 新增逻辑
          await request.post('/leaves/', leaveForm)
          ElMessage.success('申请提交成功')
        }
        leaveDialogVisible.value = false
        loadData() // 刷新列表
      } catch (e) {
        // 错误由拦截器处理
      } finally {
        submitting.value = false
      }
    }
  })
}

// 销假逻辑
const handleReportBack = (row) => {
  ElMessageBox.confirm('确认您已返校并进行销假操作吗？', '销假确认', {
    confirmButtonText: '确认销假',
    cancelButtonText: '取消',
    type: 'success'
  }).then(async () => {
    await request.post(`/leaves/${row.id}/report_back/`)
    ElMessage.success('销假成功')
    loadData()
  })
}

// --- 辅助函数 ---
const getStatusTag = (s) => {
  const map = {
    approved: 'success',
    rejected: 'danger',
    pending: 'info',
    returned: 'warning',  // 退回
    reported: 'primary',  // 已销假
    canceled: 'info'
  }
  return map[s] || 'info'
}

const getStatusText = (s) => {
  const map = {
    pending: '待审批',
    approved: '已准假',
    rejected: '已驳回',
    returned: '需修改',
    reported: '已销假',
    canceled: '已撤销'
  }
  return map[s] || s
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
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

/* 蓝色渐变卡片样式 */
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