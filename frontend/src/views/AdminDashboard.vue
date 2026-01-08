<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="200px" class="aside">
        <div class="side-content">
          <h3 class="side-title">系统管理</h3>
          <el-menu default-active="1" background-color="#304156" text-color="#fff">
            <el-menu-item index="1">
              <el-icon><User /></el-icon> 账户管理
            </el-menu-item>
          </el-menu>

          <div class="logout-wrapper">
            <el-button type="danger" plain icon="SwitchButton" @click="handleLogout" style="width: 80%">
              退出登录
            </el-button>
          </div>
        </div>
      </el-aside>

      <el-main>
        <el-card shadow="never">
          <template #header>
            <div class="header-tools">
              <span class="title">全校账户列表</span>
              <el-input
                v-model="search"
                placeholder="搜索姓名/学号"
                style="width: 250px"
                clearable
                prefix-icon="Search"
              />
            </div>
          </template>

          <el-table :data="filteredUsers" style="width: 100%" v-loading="loading">
            <el-table-column prop="student_id" label="学号/工号" width="140" />
            <el-table-column prop="username" label="姓名" width="120" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="scope">
                <el-tag :type="roleMap[scope.row.role].type" size="small">
                  {{ roleMap[scope.row.role].label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="college" label="学院" show-overflow-tooltip />

            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <div class="table-operators">
                  <el-button size="small" link type="primary" @click="editUser(scope.row)">
                    编辑
                  </el-button>
                  <el-divider direction="vertical" />
                  <el-dropdown trigger="click">
                    <el-button size="small" link type="primary">
                      更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="handleResetPassword(scope.row)">
                          <el-icon><RefreshRight /></el-icon>重置密码
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          style="color: #F56C6C"
                          @click="deleteUser(scope.row)"
                        >
                          <el-icon><Delete /></el-icon>删除账户
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-dialog v-model="editDialogVisible" title="编辑用户信息" width="500px">
          <el-form :model="editForm" label-width="100px">
            <el-form-item label="姓名">
              <el-input v-model="editForm.username" />
            </el-form-item>
            <el-form-item label="学号/工号">
              <el-input v-model="editForm.student_id" />
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="editForm.role" style="width: 100%">
                <el-option label="学生" value="student" />
                <el-option label="辅导员" value="teacher" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-form-item>
            <el-form-item label="学院">
              <el-input v-model="editForm.college" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="submitLoading" @click="submitEdit">保存</el-button>
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
import { User, Search, ArrowDown, RefreshRight, Delete, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const users = ref([])
const search = ref('')
const loading = ref(false)

// 编辑功能相关变量
const editDialogVisible = ref(false)
const submitLoading = ref(false)
const editForm = reactive({
  id: '',
  username: '',
  student_id: '',
  role: '',
  college: ''
})

const roleMap = {
  admin: { label: '管理员', type: 'danger' },
  teacher: { label: '辅导员', type: 'warning' },
  student: { label: '学生', type: 'primary' }
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await request.get('/auth/users/')
    users.value = res
  } finally {
    loading.value = false
  }
}

const filteredUsers = computed(() =>
  users.value.filter(u =>
    u.username.includes(search.value) ||
    (u.student_id && u.student_id.includes(search.value))
  )
)

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定退出系统吗？', '提示').then(() => {
    localStorage.clear()
    router.push('/login')
    ElMessage.success('已安全退出')
  }).catch(() => {})
}

// 开启编辑弹窗
const editUser = (row) => {
  editDialogVisible.value = true
  // 使用 Object.assign 深拷贝数据，避免实时修改表格数据
  Object.assign(editForm, row)
}

// 提交编辑内容
const submitEdit = async () => {
  submitLoading.value = true
  try {
    await request.patch(`/auth/users/${editForm.id}/`, editForm)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchUsers() // 刷新列表
  } catch (err) {
    ElMessage.error('更新失败')
  } finally {
    submitLoading.value = false
  }
}

const deleteUser = (row) => {
  ElMessageBox.confirm(
    `确定删除用户 [${row.username}] 吗？此操作不可逆！`,
    '危险操作',
    { confirmButtonClass: 'el-button--danger', type: 'error' }
  ).then(async () => {
    await request.delete(`/auth/users/${row.id}/`)
    ElMessage.success('用户已从系统中移除')
    fetchUsers()
  }).catch(() => {})
}

const handleResetPassword = (row) => {
  ElMessageBox.confirm(
    `确定要将用户 [${row.username}] 的密码重置为默认值吗？`,
    '密码重置',
    { type: 'warning' }
  ).then(async () => {
    try {
      const res = await request.post(`/auth/users/${row.id}/reset-password/`)
      ElMessageBox.alert(res.detail, '操作成功', { type: 'success' })
    } catch (err) {
      ElMessage.error('重置失败')
    }
  }).catch(() => {})
}

onMounted(fetchUsers)
</script>

<style scoped>
.aside {
  background: #304156;
  height: 100vh;
  color: white;
  box-shadow: 2px 0 6px rgba(0,21,41,.35);
}

.side-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.side-title {
  padding: 24px;
  text-align: center;
  font-size: 18px;
  letter-spacing: 1px;
  border-bottom: 1px solid #1f2d3d;
}

.logout-wrapper {
  margin-top: auto; /* 关键：将退出按钮推至底部 */
  padding: 20px;
  text-align: center;
  border-top: 1px solid #1f2d3d;
}

.header-tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title { font-weight: bold; color: #303133; }

.table-operators {
  display: flex;
  align-items: center;
}

.el-dropdown-menu__item .el-icon {
  margin-right: 8px;
}
</style>