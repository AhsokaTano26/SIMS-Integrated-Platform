<template>
  <div class="common-layout">
    <el-container class="layout-container">
      <el-aside width="240px" class="aside">
        <div class="logo-box">
          <div class="logo-circle">
            <el-icon><School /></el-icon>
          </div>
          <span class="logo-text">智慧管理学生端</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          background-color="#111a2c"
          text-color="#9ca3af"
          active-text-color="#ffffff"
          class="el-menu-vertical"
          @select="handleMenuSelect"
        >
          <el-menu-item index="overview">
            <el-icon><Monitor /></el-icon>
            <span>工作台</span>
          </el-menu-item>

          <el-menu-item index="personal">
            <el-icon><User /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container class="main-container">
        <el-header class="dashboard-header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ menuTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <div class="user-profile">
              <el-avatar :size="32" :src="getFullAvatarUrl(profileForm.avatar_url)" class="user-avatar" />
              <el-dropdown trigger="click">
                <span class="el-dropdown-link">
                  {{ profileForm.username }}
                  <el-icon class="el-icon--right"><arrow-down /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>

        <el-main class="dashboard-main">
          
          <div v-if="activeMenu === 'overview'">
            <el-row :gutter="20" class="stat-row">
              <el-col :span="8">
                <div class="stat-card">
                  <div class="icon-box blue"><el-icon><Timer /></el-icon></div>
                  <div class="stat-info">
                    <div class="label">待审批请假申请</div>
                    <div class="value">2</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-card">
                  <div class="icon-box green"><el-icon><Calendar /></el-icon></div>
                  <div class="stat-info">
                    <div class="label">请假天数</div>
                    <div class="value">7</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-card">
                  <div class="icon-box orange"><el-icon><Warning /></el-icon></div>
                  <div class="stat-info">
                    <div class="label">本月异常打卡</div>
                    <div class="value">0</div>
                  </div>
                </div>
              </el-col>
            </el-row>

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
                    <el-table-column label="操作" width="100" fixed="right">
                      <template #default="scope">
                        <el-button v-if="scope.row.status === 'pending'" type="danger" size="small" link @click="handleCancel(scope.row)">撤销</el-button>
                        <el-button v-else-if="scope.row.status === 'approved' && !scope.row.report_back_time" type="success" size="small" link @click="handleReportBack(scope.row)">销假</el-button>
                        <el-button v-else-if="scope.row.status === 'returned'" type="warning" size="small" link @click="handleEdit(scope.row)">修改</el-button>
                        <span v-else-if="scope.row.report_back_time" style="color: #67C23A; font-size: 12px;">已返校</span>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <div v-if="activeMenu === 'personal'" class="profile-page">
            <el-row :gutter="20">
              <el-col :md="8" :xs="24">
                <el-card class="box-card profile-side-card" shadow="hover">
                  <div class="profile-header-box">
                    <div class="avatar-wrapper" @click="triggerUpload">
                      <el-avatar :size="100" :src="getFullAvatarUrl(profileForm.avatar_url)" />
                      <div class="avatar-hover">更换头像</div>
                    </div>
                    <input type="file" ref="fileInput" style="display: none" @change="handleFileChange" accept="image/*" />
                    <h2 class="user-name">{{ profileForm.username }}</h2>
                    <el-tag size="small" effect="dark" style="margin-bottom: 15px;">{{ profileForm.major }}</el-tag>
                    <div class="info-list">
                      <p><el-icon><Postcard /></el-icon> 学号：{{ profileForm.student_id }}</p>
                      <p><el-icon><Location /></el-icon> 宿舍：{{ profileForm.dormitory_name || '未录入' }}</p>
                    </div>
                  </div>
                </el-card>
              </el-col>

              <el-col :md="16" :xs="24">
                <el-card class="box-card" shadow="hover">
                  <template #header>
                    <div class="card-header"><span>基本资料修改</span></div>
                  </template>
                  <el-form :model="profileForm" label-width="100px" label-position="left">
                    <el-row :gutter="20">
                      <el-col :span="12">
                        <el-form-item label="姓名">
                          <el-input v-model="profileForm.username" />
                        </el-form-item>
                      </el-col>
                      <el-col :span="12">
                        <el-form-item label="性别">
                          <el-radio-group v-model="profileForm.gender">
                            <el-radio label="male">男</el-radio>
                            <el-radio label="female">女</el-radio>
                          </el-radio-group>
                        </el-form-item>
                      </el-col>
                    </el-row>
                    <el-form-item label="手机号码">
                      <el-input v-model="profileForm.phone" placeholder="请输入常用手机号" />
                    </el-form-item>
                    <el-row :gutter="20">
                      <el-col :span="12">
                        <el-form-item label="所属学院">
                          <el-input v-model="profileForm.college" disabled />
                        </el-form-item>
                      </el-col>
                      <el-col :span="12">
                        <el-form-item label="年级专业">
                          <el-input :value="profileForm.grade + '级 ' + profileForm.major" disabled />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    <el-form-item label="辅导员">
                      <el-tag type="info" plain>{{ profileForm.instructor_name || '暂无数据' }}</el-tag>
                    </el-form-item>
                    <el-form-item style="margin-top: 20px;">
                      <el-button type="primary" :loading="updating" @click="handleUpdateProfile">保存修改</el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
              </el-col>
            </el-row>
          </div>

        </el-main>
      </el-container>
    </el-container>

    <el-dialog v-model="leaveDialogVisible" :title="isEditMode ? '修改申请' : '发起请假申请'" width="500px">
      <el-form :model="leaveForm" :rules="leaveRules" ref="leaveFormRef" label-width="80px">
        <el-form-item label="请假去向" prop="leave_for">
          <el-input v-model="leaveForm.leave_for" placeholder="请输入具体请假去向" />
        </el-form-item>        
        <el-form-item label="请假事由" prop="reason">
          <el-input v-model="leaveForm.reason" type="textarea" :rows="3" placeholder="请详细说明请假原因..." />
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
import { ref, reactive, onMounted,computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Location, Position, School, Reading, User, ArrowDown, UserFilled,Postcard, Plus, Camera } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const activeMenu = ref('overview')

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

const pendingCount = computed(() => {
  return leaveList.value.filter(item => 
    item.status === 'pending' || item.status === 'returned'
  ).length
})
const menuTitle = computed(() => {
  const map = { overview: '工作台',personal:"个人信息"}
  return map[activeMenu.value]
})
const handleMenuSelect = (index) => {
  activeMenu.value = index
  // 如果你有配置路由，也可以加上 router.push，但这里用 v-if 只要改变 activeMenu 即可切换内容
}
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
const logout = () => {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
/* 1. 布局基础结构 */
.layout-container {
  height: 100vh;
}

/* 2. 侧边栏 Aside 深度优化 */
.aside {
  background-color: #111a2c; /* 深蓝背景 */
  transition: width 0.3s;
  overflow: hidden;
  border-right: none;
  display: flex;
  flex-direction: column;
}

/* 仿教师端 Logo 盒子 */
.logo-box {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  background: #111a2c;
}

/* 蓝色圆角图标背景 */
.logo-circle {
  width: 32px;
  height: 32px;
  background: #409eff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  flex-shrink: 0;
}

.logo-text {
  color: #fff;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

/* 3. 菜单 El-Menu 美化 */
.el-menu-vertical {
  border-right: none;
  padding: 0 10px; /* 增加整体边距，让菜单项不贴边 */
}

/* 菜单项基础样式 */
:deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 4px 0;
  border-radius: 8px;
  color: #9ca3af !important; /* 未选中时的灰色 */
  transition: all 0.3s;
}

/* 鼠标悬停 */
:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: #fff !important;
}

/* 激活状态：蓝色背景块 + 白色文字 */
:deep(.el-menu-item.is-active) {
  background-color: #409eff !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3); /* 蓝色发光阴影 */
}

/* 4. 顶部 Header 样式优化 */
.dashboard-header {
  background-color: #ffffff;
  color: #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05); /* 更轻柔的投影 */
  z-index: 10;
  border-bottom: 1px solid #f0f0f0;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
}

/* 自动高亮的 Breadcrumb */
:deep(.el-breadcrumb__inner) {
  font-size: 14px;
  color: #606266;
}

/* 右侧用户信息 */
.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 20px;
  transition: background 0.3s;
}

.user-profile:hover {
  background-color: #f5f7fa;
}

.el-dropdown-link {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #303133;
  outline: none;
}

/* 5. 主内容区域与卡片美化 */
/* 1. 背景与整体间距优化 */
.dashboard-main {
  background-color: #f6f8fb; /* 更有高级感的浅蓝灰底色 */
  padding: 30px; /* 增加主区域内边距 */
  overflow-y: auto;
}

/* 2. 统计卡片 (Stat Cards) 优化 */
.stat-row {
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  padding: 24px; /* 加大内边距 */
  border-radius: 16px; /* 更大的圆角 */
  display: flex;
  align-items: center;
  gap: 20px;
  /* 关键：柔和的阴影 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.icon-box {
  width: 56px; /* 稍微放大图标容器 */
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-info .label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 6px;
}

.stat-info .value {
  font-size: 28px; /* 数字加大 */
  font-weight: 700; /* 数字加粗 */
  color: #1a1a1a;
  line-height: 1;
}

/* 3. 业务功能卡片 (Box Cards) 优化 */
.box-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  margin-bottom: 24px;
  background: #fff;
}

/* 标题栏对齐与美化 */
:deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f2f5;
  font-size: 16px;
  font-weight: 600;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 4. 打卡组件特定美化 */
/* 打卡卡片容器 - 增加高度和呼吸感 */
.attendance-content {
  padding: 40px 24px; 
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px; /* 保证卡片有足够的高度，显得大方 */
}

/* 中间空状态/提示区域 */
.checkin-empty {
  text-align: center;
  margin-bottom: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 定位图标美化 - 增加一个浅色圆形背景 */
.checkin-empty .el-icon {
  background: #f0f7ff; /* 极其清爽的浅蓝色 */
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #409eff; /* 图标主色 */
  font-size: 40px !important;
  margin-bottom: 20px;
  transition: all 0.3s;
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.1);
}

/* 提示文字美化 */
.checkin-empty p {
  color: #909399;
  font-size: 15px;
  max-width: 220px;
  line-height: 1.6;
}

/* 打卡按钮 - 升级为渐变色和更有质感的投影 */
.attendance-content .el-button--primary {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  border: none;
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  box-shadow: 0 8px 20px -6px rgba(64, 158, 255, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 按钮悬浮效果 */
.attendance-content .el-button--primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 24px -6px rgba(64, 158, 255, 0.5);
  filter: brightness(1.05);
}

/* 按钮点击激活效果 */
.attendance-content .el-button--primary:active {
  transform: translateY(1px);
}

/* 打卡结果（el-result）适配 */
:deep(.el-result) {
  padding: 0;
  margin-bottom: 20px;
}

:deep(.el-result__title p) {
  font-size: 20px;
  font-weight: bold;
}

/* 8. 响应式处理 */
@media (max-width: 768px) {
  .aside { width: 64px !important; }
  .logo-text { display: none; }
}
/* ============================================================
   6. 个人中心 (Profile Page) 深度美化
   ============================================================ */

/* 1. 头像容器：彻底解决马赛克透明网格问题 */
.avatar-wrapper {
  position: relative;
  width: 110px;  /* 稍微加大 */
  height: 110px;
  margin: 10px auto 20px;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
  background-color: #ffffff; /* 关键：设置白色底色，防止透明图显示马赛克 */
  border: 4px solid #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.avatar-wrapper:hover {
  transform: scale(1.02);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.2);
}

/* 2. 更换头像文字：改为高级的悬浮遮罩 */
.avatar-hover-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5); /* 半透明黑色 */
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  opacity: 0; /* 平时隐藏 */
  transition: opacity 0.3s;
  font-size: 13px;
  backdrop-filter: blur(2px); /* 轻微模糊效果 */
}

.avatar-wrapper:hover .avatar-hover-mask {
  opacity: 1; /* 悬浮显示 */
}

.avatar-hover-mask .el-icon {
  font-size: 20px;
  margin-bottom: 4px;
}

/* 3. 左侧信息展示栏美化 */
.profile-side-card {
  text-align: center;
  padding-bottom: 20px;
}

.user-name {
  margin: 12px 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: #2c3e50;
}

.major-tag {
  margin-bottom: 25px;
  border-radius: 6px;
  font-weight: 500;
}

/* 左侧信息条目垂直排版 */
.info-list-vertical {
  text-align: left;
  padding: 0 15px;
  margin-top: 20px;
}

.info-list-vertical p {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
  padding: 8px 12px;
  background: #f8faff; /* 给每一行加一个极浅的背景 */
  border-radius: 8px;
}

.info-list-vertical .el-icon {
  margin-right: 12px;
  color: #409eff;
  font-size: 16px;
}

.info-list-vertical b {
  color: #909399;
  font-weight: 500;
  width: 50px;
  flex-shrink: 0;
}

/* 4. 右侧资料修改表单美化 */
:deep(.el-divider__text) {
  background-color: #fff;
  color: #409eff;
  font-weight: bold;
}

.profile-page .el-form-item {
  margin-bottom: 22px;
}

/* 禁用状态的输入框美化 */
:deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #fcfcfc;
  box-shadow: none;
  border: 1px solid #f0f0f0;
}

/* 保存按钮 */
.profile-page .el-button--primary {
  padding: 12px 30px;
  height: auto;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  margin-top: 10px;
}
</style>