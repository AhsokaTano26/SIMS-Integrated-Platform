<template>
  <div class="admin-layout">
    <el-container class="layout-container">
      <el-aside width="220px" class="aside">
        <div class="logo-area">
          <el-icon><Refrigerator /></el-icon>
          <span v-if="!isCollapse">智慧后台</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          class="el-menu-vertical"
          @select="handleMenuSelect"
        >
          <el-menu-item index="user">
            <el-icon><User /></el-icon>
            <span>用户与权限管理</span>
          </el-menu-item>

          <el-menu-item index="dorm">
            <el-icon><OfficeBuilding /></el-icon>
            <span>宿舍楼宇管理</span>
          </el-menu-item>

          <el-menu-item index="attendance">
            <el-icon><LocationInformation /></el-icon>
            <span>全校查寝监控</span>
          </el-menu-item>

          <el-menu-item index="leave">
            <el-icon><DocumentChecked /></el-icon>
            <span>学生请假中心</span>
          </el-menu-item>
        </el-menu>

        <div class="logout-wrapper">
          <el-button type="danger" plain icon="SwitchButton" @click="handleLogout" style="width: 100%">
            退出系统
          </el-button>
        </div>
      </el-aside>

      <el-main class="main-content">
        <el-card shadow="never" v-if="activeMenu === 'user'" class="content-card">
          <template #header>
            <div class="header-tools">
              <span class="card-title">全校账户列表</span>
              <div class="tools-right">
                <el-input
                  v-model="search"
                  placeholder="搜索姓名/学号"
                  style="width: 200px; margin-right: 10px;"
                  clearable
                  prefix-icon="Search"
                />
                <el-button type="primary" icon="Plus" @click="openCreateUserDialog">新建用户</el-button>
              </div>
            </div>
          </template>

          <el-table :data="filteredUsers" style="width: 100%" v-loading="loading" border stripe>
            <el-table-column prop="student_id" label="学号/工号" width="140" />
            <el-table-column prop="username" label="姓名" width="120" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="scope">
                <el-tag :type="roleMap[scope.row.role]?.type || 'info'" size="small">
                  {{ roleMap[scope.row.role]?.label || scope.row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="college" label="学院/部门" show-overflow-tooltip />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" type="primary" link @click="editUser(scope.row)">编辑</el-button>
                <el-button size="small" type="warning" link @click="handleResetPassword(scope.row)">重置密码</el-button>
                <el-button size="small" type="danger" link @click="deleteUser(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" v-if="activeMenu === 'dorm'" class="content-card">
          <template #header>
            <div class="header-tools">
              <span class="card-title">宿舍楼宇信息库</span>
              <el-button type="primary" icon="Plus" @click="openDormDialog">录入新宿舍楼</el-button>
            </div>
          </template>

          <el-table :data="dormList" style="width: 100%" border v-loading="loading">
            <el-table-column prop="buildingName" label="楼宇名称" width="180" />
            <el-table-column prop="buildingCode" label="楼宇编号" width="150" />
            <el-table-column label="地理位置 (经纬度)">
              <template #default="scope">
                <el-tag size="small" type="success">{{ scope.row.latitude }}, {{ scope.row.longitude }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" width="180" />
          </el-table>
        </el-card>

        <el-card shadow="never" v-if="activeMenu === 'attendance'" class="content-card">
          <template #header>
            <div class="header-tools">
              <span class="card-title">全校学生打卡实时监控</span>
              <el-date-picker v-model="filterDate" type="date" placeholder="选择日期" />
            </div>
          </template>

          <el-table :data="attendanceList" style="width: 100%" stripe border>
            <el-table-column prop="studentName" label="学生姓名" width="120" />
            <el-table-column prop="studentId" label="学号" width="140" />
            <el-table-column prop="dormName" label="所属宿舍" width="150" />
            <el-table-column prop="checkInTime" label="打卡时间" width="180" sortable />
            <el-table-column prop="location" label="打卡地点" show-overflow-tooltip />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === '正常' ? 'success' : 'danger'">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" v-if="activeMenu === 'leave'" class="content-card">
          <template #header>
            <div class="header-tools">
              <span class="card-title">全校请假审批记录</span>
              <el-radio-group v-model="leaveFilter" size="small">
                <el-radio-button label="all">全部</el-radio-button>
                <el-radio-button label="pending">待审批</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <el-table :data="leaveList" style="width: 100%" border>
            <el-table-column prop="studentName" label="申请人" width="120" />
            <el-table-column prop="type" label="请假类型" width="100">
              <template #default="scope">
                <el-tag effect="plain">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="请假时间段" width="300">
              <template #default="scope">
                {{ scope.row.startTime }} 至 {{ scope.row.endTime }}
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="请假原因" show-overflow-tooltip />
            <el-table-column label="审批状态" width="100">
               <template #default="scope">
                <span :style="{color: scope.row.status === '待审批' ? '#E6A23C' : '#67C23A'}">● {{ scope.row.status }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-dialog v-model="userDialogVisible" :title="isEditMode ? '编辑用户信息' : '创建新用户'" width="500px">
          <el-form :model="userForm" label-width="100px" ref="userFormRef">
            <el-form-item label="姓名" required>
              <el-input v-model="userForm.username" placeholder="请输入真实姓名" />
            </el-form-item>
            <el-form-item label="学号/工号" required>
              <el-input v-model="userForm.student_id" placeholder="作为登录账号" />
            </el-form-item>
            <el-form-item label="初始密码" required v-if="!isEditMode">
              <el-input v-model="userForm.password" type="password" show-password placeholder="设置初始登录密码" />
            </el-form-item>
            <el-form-item label="角色" required>
              <el-select v-model="userForm.role" style="width: 100%">
                <el-option label="学生" value="student" />
                <el-option label="辅导员" value="teacher" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-form-item>
            <el-form-item label="学院/部门">
              <el-input v-model="userForm.college" placeholder="例如：计算机学院" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="userDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="submitLoading" @click="handleUserSubmit">保存</el-button>
          </template>
        </el-dialog>

        <el-dialog v-model="dormDialogVisible" title="录入新宿舍楼信息" width="500px">
          <el-form :model="dormForm" label-width="100px">
            <el-form-item label="楼宇名称">
              <el-input v-model="dormForm.name" placeholder="例：南区一号楼" />
            </el-form-item>
            <el-form-item label="楼宇编号">
              <el-input v-model="dormForm.code" placeholder="例：S1" />
            </el-form-item>
            <el-form-item label="经度 (Lng)">
              <el-input-number v-model="dormForm.longitude" :precision="6" :step="0.00001" style="width: 100%" />
            </el-form-item>
            <el-form-item label="纬度 (Lat)">
              <el-input-number v-model="dormForm.latitude" :precision="6" :step="0.00001" style="width: 100%" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="dormDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitDorm">确认录入</el-button>
          </template>
        </el-dialog>

      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Search, RefreshRight, Delete, SwitchButton, OfficeBuilding, LocationInformation, DocumentChecked, Plus,
  Refrigerator
} from '@element-plus/icons-vue'

const router = useRouter()
const activeMenu = ref('user') // 默认显示用户管理
const loading = ref(false)

// ----------------- 用户管理逻辑 -----------------
const users = ref([])
const search = ref('')
const userDialogVisible = ref(false)
const isEditMode = ref(false)
const submitLoading = ref(false)
const userForm = reactive({
  id: '',
  username: '',
  student_id: '',
  password: '', // 仅用于创建
  role: 'student',
  college: ''
})

const roleMap = {
  admin: { label: '管理员', type: 'danger' },
  teacher: { label: '辅导员', type: 'warning' },
  student: { label: '学生', type: 'primary' }
}

const filteredUsers = computed(() =>
  users.value.filter(u =>
    u.username.includes(search.value) ||
    (u.student_id && u.student_id.includes(search.value))
  )
)

const fetchUsers = async () => {
  if (activeMenu.value !== 'user') return
  loading.value = true
  try {
    const res = await request.get('/auth/users/')
    users.value = res
  } catch(e) {
    // 模拟数据（如果后端没通）
    // users.value = [
    //   { id: 1, username: '张三', student_id: '2020001', role: 'student', college: '计算机学院' },
    //   { id: 2, username: '李老师', student_id: '1001', role: 'teacher', college: '学工处' }
    // ]
  } finally {
    loading.value = false
  }
}

// 打开创建用户弹窗
const openCreateUserDialog = () => {
  isEditMode.value = false
  Object.assign(userForm, { id: '', username: '', student_id: '', password: '', role: 'student', college: '' })
  userDialogVisible.value = true
}

// 打开编辑用户弹窗
const editUser = (row) => {
  isEditMode.value = true
  Object.assign(userForm, row)
  userDialogVisible.value = true
}

// 提交用户 (新增或编辑)
const handleUserSubmit = async () => {
  submitLoading.value = true
  try {
    if (isEditMode.value) {
      await request.patch(`/auth/users/${userForm.id}/`, userForm)
      ElMessage.success('用户信息更新成功')
    } else {
      await request.post('/auth/users/', userForm)
      ElMessage.success('新用户创建成功')
    }
    userDialogVisible.value = false
    fetchUsers()
  } catch (err) {
    ElMessage.error(isEditMode.value ? '更新失败' : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

const deleteUser = (row) => {
  ElMessageBox.confirm(`确定删除用户 [${row.username}] 吗？`, '警告', { type: 'warning' })
    .then(async () => {
      await request.delete(`/auth/users/${row.id}/`)
      ElMessage.success('已删除')
      fetchUsers()
    }).catch(() => {})
}

const handleResetPassword = (row) => {
  ElMessageBox.confirm(`重置 [${row.username}] 的密码为 "123456"？`, '重置密码', { type: 'warning' })
    .then(async () => {
      await request.post(`/auth/users/${row.id}/reset-password/`)
      ElMessage.success('密码重置成功')
    }).catch(() => {})
}

// ----------------- 宿舍管理逻辑 -----------------
const dormDialogVisible = ref(false)
const dormList = ref([]) // 这里应该从后端获取
const dormForm = reactive({ name: '', code: '', latitude: 0, longitude: 0 })

const fetchDorms = async () => {
  // loading.value = true
  // const res = await request.get('/dorm/buildings/')
  // dormList.value = res

  // 模拟数据
  dormList.value = [
    { buildingName: '南区一号楼', buildingCode: 'S1', latitude: 30.5, longitude: 114.3, createTime: '2023-01-01' }
  ]
}

const openDormDialog = () => {
  Object.assign(dormForm, { name: '', code: '', latitude: 0, longitude: 0 })
  dormDialogVisible.value = true
}

const submitDorm = async () => {
  try {
    await request.post('/dorm/buildings/', dormForm)
    ElMessage.success('宿舍楼录入成功')
    dormDialogVisible.value = false
    fetchDorms()
  } catch (e) {
    ElMessage.error('录入失败')
  }
}

// ----------------- 考勤与请假 (只读数据展示) -----------------
const attendanceList = ref([])
const leaveList = ref([])
const filterDate = ref(new Date())
const leaveFilter = ref('all')

const fetchAttendance = async () => {
  // const res = await request.get('/attendance/all')
  // attendanceList.value = res
  attendanceList.value = [
    { studentName: '王五', studentId: '2020002', dormName: 'S1-303', checkInTime: '2023-10-25 21:30:00', location: '宿舍S1', status: '正常' },
    { studentName: '赵六', studentId: '2020003', dormName: 'S1-304', checkInTime: '', location: '', status: '缺卡' }
  ]
}

const fetchLeaves = async () => {
  // const res = await request.get('/leave/all')
  // leaveList.value = res
  leaveList.value = [
    { studentName: '孙七', type: '病假', startTime: '2023-10-25', endTime: '2023-10-27', reason: '发烧去医院', status: '待审批' },
    { studentName: '周八', type: '事假', startTime: '2023-10-20', endTime: '2023-10-21', reason: '家里有事', status: '已通过' }
  ]
}

// ----------------- 通用逻辑 -----------------
const handleMenuSelect = (index) => {
  activeMenu.value = index
  if (index === 'user') fetchUsers()
  if (index === 'dorm') fetchDorms()
  if (index === 'attendance') fetchAttendance()
  if (index === 'leave') fetchLeaves()
}

const handleLogout = () => {
  ElMessageBox.confirm('确定退出系统吗？', '提示').then(() => {
    localStorage.clear()
    router.push('/login')
  }).catch(() => {})
}

onMounted(() => {
  fetchUsers() // 默认加载用户
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
}

.aside {
  background: #304156;
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow-x: hidden;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
  z-index: 10;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b3649;
  font-weight: bold;
  font-size: 18px;
  color: #fff;
  gap: 10px;
}
.logo-img { width: 30px; }

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.logout-wrapper {
  padding: 20px;
  background: #263445;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  height: 100vh;
  overflow-y: auto;
}

.content-card {
  min-height: calc(100vh - 40px);
  border-radius: 8px;
}

.header-tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.tools-right {
  display: flex;
  align-items: center;
}
</style>