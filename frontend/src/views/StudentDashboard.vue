<template>
  <div class="common-layout">
    <el-container>
      <el-header class="dashboard-header">
        <div class="logo">🏫 智慧校园学生端</div>
        <div class="user-info">
          <el-tag type="success" effect="plain" class="role-tag">学生</el-tag>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="el-dropdown-link">
              <span class="username-wrapper">{{ profileForm.username }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
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
              <el-avatar 
                :size="70" 
                :src="getFullAvatarUrl(profileForm.avatar_url)"
                class="custom-avatar"
                @click="triggerUpload"
                style="cursor: pointer;"
              >
                <el-icon :size="40"><UserFilled /></el-icon>
              </el-avatar>
            </div>
            <input
              type="file"
              ref="fileInput"
              style="display: none"
              accept="image/*"
              @change="handleFileChange"
            />
            <div class="welcome-box">
              <div class="user-title">
                <span class="name">{{ profileForm.username }}！欢迎回来</span>
                <el-tag size="small" effect="dark" class="gender-tag">
                  {{ profileForm.gender === 'female' ? '♀ 女' : (profileForm.gender === 'male' ? '♂ 男' : '⚪ 未知') }}
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
                      v-if="scope.row.status === 'pending'"
                      type="danger" 
                      size="small" link
                      @click="handleCancel(scope.row)"
                    >撤销</el-button>
                    <el-button
                      v-else-if="scope.row.status === 'approved' && !scope.row.report_back_time"
                      type="success" size="small" link
                      @click="handleReportBack(scope.row)"
                    >销假</el-button>
                    <el-button
                      v-else-if="scope.row.status === 'returned'"
                      type="warning" size="small" link
                      @click="handleEdit(scope.row)"
                    >修改</el-button>
                    <span v-else-if="scope.row.report_back_time" style="color: #67C23A; font-size: 12px;">已返校</span>
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

    <el-dialog v-model="leaveDialogVisible" :title="isEditMode ? '修改申请' : '发起请假申请'" width="500px">
      <el-form :model="leaveForm" :rules="leaveRules" ref="leaveFormRef" label-width="80px">
        <el-form-item label="请假去向" prop="leave_for">
          <el-input v-model="leaveForm.leave_for" placeholder="请输入具体请假去向" />
        </el-form-item>        
        <el-form-item label="请假事由" prop="reason">
          <el-input v-model="leaveForm.reason" type="textarea" :rows="3" placeholder="请详细说明请假原因..." />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker v-model="leaveForm.start_time" type="datetime" placeholder="选择离校时间" style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item label="预计返回" prop="end_time">
          <el-date-picker v-model="leaveForm.end_time" type="datetime" placeholder="选择返校时间" style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
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
import { Location, Position, School, Reading, User, ArrowDown, UserFilled, Plus } from '@element-plus/icons-vue'
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
const submitting = ref(false)
const leaveFormRef = ref(null)
const isEditMode = ref(false)
const currentLeaveId = ref(null)

const fileInput = ref(null) // 新增：用于操作隐藏的 input

// 新增函数 1：处理图片地址拼接（防止后端返回相对路径导致无法显示）
const getFullAvatarUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const baseUrl = `http://127.0.0.1:8000${url}`
  // 核心：添加时间戳，防止浏览器缓存旧头像
  // 结果示例：http://127.0.0.1:8000/media/avatars/1.jpg?t=1704888888
  return `${baseUrl}?t=${new Date().getTime()}`
}

// 新增函数 2：触发点击
const triggerUpload = () => {
  if (fileInput.value) {
    fileInput.value.click()
  } else {
    console.error("文件输入框未找到")
  }
}

// 新增函数 3：核心上传逻辑
const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 简单的文件校验
  const isJPGorPNG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPGorPNG) {
    ElMessage.error('上传头像图片只能是 JPG 或 PNG 格式!')
    return
  }
  if (!isLt2M) {
    ElMessage.error('上传头像图片大小不能超过 2MB!')
    return
  }

  // 构建 FormData（上传文件必须使用这个格式）
  const formData = new FormData()
  formData.append('avatar', file) // 'avatar' 必须对应 Django Model 中的字段名

try {
    await request.patch(`/auth/users/${profileForm.id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    ElMessage.success('头像更换成功！')

    await loadData() 
  } catch (err) {
    ElMessage.error('头像上传失败')
  } 
}
// 在这里增加 leave_for
const leaveForm = reactive({ 
  reason: '', 
  leave_for: '', // 新增：请假去向
  start_time: '', 
  end_time: '' 
})

// 修改校验规则
const leaveRules = {
  reason: [{ required: true, message: '请输入请假事由', trigger: 'blur' }],
  leave_for: [{ required: true, message: '请输入请假去向', trigger: 'blur' }], // 新增规则
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

const profileForm = reactive({
  id: '', username: '', student_id: '', college: '', major: '',
  grade: '', class_name: '', phone: '', gender: '', instructor_name: '',
  // 新增字段
  avatar_url: '',    // 对应后端
  dormitory_name: '', // 建议后端 Serializer 返回宿舍楼名称
  address: ''        // 详细地址
})

// --- 数据加载 ---
const loadData = async () => {
  loadingList.value = true
  try {
    const [userRes, leaveRes] = await Promise.all([
      request.get('/auth/users/me/'),
      request.get('/leaves/')
    ])
    Object.assign(profileForm, userRes)
    leaveList.value = leaveRes
  } catch (err) {
    ElMessage.error('数据加载失败')
  } finally {
    loadingList.value = false
  }
}

onMounted(loadData)

// --- 个人信息处理 ---
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

// --- 打卡逻辑 ---
const startCheckIn = () => {
  locating.value = true
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持定位功能')
    locating.value = false
    return
  }
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const { latitude, longitude } = position.coords
        const res = await request.post('/attendance/', { lat: latitude, lng: longitude })
        checkStatus.value = res
        if (res.is_normal) ElMessage.success('打卡成功')
        else ElMessage.warning(res.msg)
      } catch (err) {
        ElMessage.error('打卡失败：' + (err.response?.data?.detail || '服务器异常'))
      } finally {
        locating.value = false
      }
    },
    (error) => {
      locating.value = false
      ElMessage.error("定位失败，请确保已开启位置权限")
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

// --- 请假逻辑 ---
// --- 学生撤销请假逻辑 ---
const handleCancel = (row) => {
  ElMessageBox.confirm(
    '确定要撤销这条请假申请吗？撤销后老师将无法看到此申请。',
    '撤销确认',
    {
      confirmButtonText: '确认撤销',
      cancelButtonText: '点错了',
      type: 'warning',
    }
  ).then(async () => {
    try {
      // 调用后端定义的 @action(detail=True, methods=['post']) cancel 接口
      // URL 对应为 /leaves/{id}/cancel/
      await request.post(`/leaves/${row.id}/cancel/`)
      ElMessage.success('申请已成功撤销')
      loadData() // 刷新列表
    } catch (err) {
      ElMessage.error('撤销失败：' + (err.response?.data?.detail || '系统异常'))
    }
  }).catch(() => {
    // 点击取消不需要任何操作
  })
}
const openLeaveDialog = () => {
  isEditMode.value = false
  leaveForm.leave_for = '' // 新增
  leaveForm.reason = ''
  leaveForm.start_time = ''
  leaveForm.end_time = ''
  leaveDialogVisible.value = true
}

const handleEdit = (row) => {
  isEditMode.value = true
  currentLeaveId.value = row.id
  leaveForm.leave_for = row.leave_for // 新增回显
  leaveForm.reason = row.reason
  leaveForm.start_time = row.start_time
  leaveForm.end_time = row.end_time
  leaveDialogVisible.value = true
}

const handleSubmitLeave = async () => {
  if (!leaveFormRef.value) return
  await leaveFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEditMode.value) {
          await request.put(`/leaves/${currentLeaveId.value}/`, { ...leaveForm, status: 'pending' })
          ElMessage.success('已重新提交申请')
        } else {
          await request.post('/leaves/', leaveForm)
          ElMessage.success('申请提交成功')
        }
        leaveDialogVisible.value = false
        loadData()
      } catch (e) {} finally {
        submitting.value = false
      }
    }
  })
}

const handleReportBack = (row) => {
  ElMessageBox.confirm('确认您已返校并进行销假操作吗？', '销假确认', {
    type: 'success'
  }).then(async () => {
    await request.post(`/leaves/${row.id}/report_back/`)
    ElMessage.success('销假成功')
    loadData()
  })
}

// --- 辅助工具 ---
const getStatusTag = (s) => {
  const map = { 
    approved: 'success', 
    rejected: 'danger', 
    pending: 'info', 
    returned: 'warning', 
    reported: 'primary',
    canceled: 'info' // 撤销状态使用灰色
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
    canceled: '已撤销' // 增加文字映射
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
.dashboard-header { background-color: #409eff; color: white; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; }
.user-profile-card { background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%); border-radius: 16px; padding: 24px; color: white; position: relative; overflow: hidden; margin-bottom: 24px; box-shadow: 0 8px 20px rgba(24, 144, 255, 0.3); }
.profile-header { display: flex; align-items: center; margin-bottom: 24px; }
/* 找到 .avatar-box，增加悬停效果 */
.avatar-box {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px;
  border-radius: 50%;
  margin-right: 16px;
  transition: all 0.3s ease; /* 增加过渡动画 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-box:hover {
  background: rgba(255, 255, 255, 0.4); /* 鼠标移上去变亮 */
  transform: scale(1.05); /* 轻微放大 */
}

.custom-avatar {
  border: 2px solid rgba(255, 255, 255, 0.3);
}
.user-title .name { font-size: 22px; font-weight: bold; display: block; margin-bottom: 8px; }
.gender-tag { background: rgba(255, 255, 255, 0.2); border: none; color: white; margin-left: 8px; }
.sub-info { font-size: 14px; opacity: 0.9; }
.role-badge { position: absolute; top: 0; right: 0; background: #36cfc9; padding: 4px 12px; font-size: 12px; border-bottom-left-radius: 12px; }
.profile-footer { display: flex; justify-content: space-between; background: rgba(0, 0, 0, 0.1); margin: 0 -24px -24px -24px; padding: 12px 24px; font-size: 14px; }
.footer-item { display: flex; align-items: center; gap: 6px; }
.dashboard-main { background-color: #f0f2f5; padding: 24px; }
.box-card { border-radius: 12px; margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
.attendance-content { text-align: center; padding: 10px; }
/* 关键：新增 user-info 样式，解决拥挤 */
.user-info {
  display: flex;
  align-items: center;
  gap: 16px; /* 在“学生”标签和“用户名”之间产生明显的呼吸间距 */
}

/* 关键：优化下拉菜单外观，移除默认焦点框 */
.el-dropdown-link {
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  outline: none; /* 移除点击时的蓝色边框 */
}

/* 关键：防止长用户名撑破布局 */
.username-wrapper {
  font-weight: 500;
  max-width: 100px; /* 用户名最长 100px，超出显示省略号 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 调整角色标签的边距，确保不再拥挤 */
.role-tag {
  margin: 0; /* 间距已由父级的 gap 处理 */
  flex-shrink: 0; /* 防止标签被压缩变形 */
}
</style>