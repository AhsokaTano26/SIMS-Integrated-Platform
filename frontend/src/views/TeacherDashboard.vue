<template>
  <div class="teacher-layout">
    <el-container>
      <el-header class="t-header">
        <div class="logo">🛡️ 辅导员管理后台</div>
        <div class="user-actions">
          <el-avatar :size="30" style="margin-right: 10px">教</el-avatar>
          <span>{{ teacherName }} 老师</span>
          <el-button type="info" size="small" link @click="logout" style="margin-left: 15px">退出</el-button>
        </div>
      </el-header>

      <el-main class="t-main">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card shadow="never">
              <template #header>
                <div class="card-header">
                  <span>📥 待处理请假申请</span>
                  <el-radio-group v-model="filterStatus" size="small" @change="fetchLeaveData">
                    <el-radio-button label="pending">待处理</el-radio-button>
                    <el-radio-button label="all">全部</el-radio-button>
                  </el-radio-group>
                </div>
              </template>

              <el-table :data="leaveTasks" v-loading="loading" stripe>
                <el-table-column prop="student_name" label="学生" width="100" />
                <el-table-column prop="reason" label="原因" show-overflow-tooltip />
                <el-table-column label="时间范围" width="280">
                  <template #default="scope">
                    {{ formatDate(scope.row.start_time) }} 至 {{ formatDate(scope.row.end_time) }}
                  </template>
                </el-table-column>
                <el-table-column label="证明" width="80">
                  <template #default="scope">
                    <el-image
                      v-if="scope.row.evidence"
                      style="width: 30px; height: 30px"
                      :src="scope.row.evidence"
                      :preview-src-list="[scope.row.evidence]"
                      preview-teleported
                    />
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="scope">
                    <template v-if="scope.row.status === 'pending'">
                      <el-button type="success" size="small" @click="handleApprove(scope.row, 'approved')">同意</el-button>
                      <el-button type="danger" size="small" @click="handleApprove(scope.row, 'rejected')">驳回</el-button>
                    </template>
                    <el-tag v-else :type="statusMap[scope.row.status].type">
                      {{ statusMap[scope.row.status].text }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card shadow="never" style="margin-bottom: 20px">
              <template #header>📊 今日考勤概况</template>
              <div class="stat-box">
                <div class="stat-item">
                  <div class="num">{{ stats.total }}</div>
                  <div class="lab">总人数</div>
                </div>
                <div class="stat-item">
                  <div class="num success">{{ stats.normal }}</div>
                  <div class="lab">正常打卡</div>
                </div>
                <div class="stat-item">
                  <div class="num danger">{{ stats.abnormal }}</div>
                  <div class="lab">位置异常</div>
                </div>
              </div>
            </el-card>

            <el-card shadow="never">
              <template #header>⚠️ 实时异常预警</template>
              <el-scrollbar height="300px">
                <div v-for="item in alerts" :key="item.id" class="alert-item">
                  <el-tag type="danger" size="small">异常</el-tag>
                  <span class="alert-info"><b>{{ item.student }}</b> 距离宿舍 {{ item.distance }}米</span>
                  <div class="time">{{ item.time }}</div>
                </div>
                <el-empty v-if="alerts.length === 0" description="暂无预警数据" />
              </el-scrollbar>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const teacherName = ref(JSON.parse(localStorage.getItem('user_info') || '{}').username)

// 状态映射
const statusMap = {
  approved: { text: '已准假', type: 'success' },
  rejected: { text: '已驳回', type: 'danger' },
  pending: { text: '待处理', type: 'info' }
}

const filterStatus = ref('pending')
const leaveTasks = ref([])
const loading = ref(false)
const stats = ref({ total: 120, normal: 115, abnormal: 5 })
const alerts = ref([])

// 获取请假审批数据
const fetchLeaveData = async () => {
  loading.value = true
  try {
    // 假设后端接口支持通过 status 过滤
    const url = filterStatus.value === 'all' ? '/leaves/' : '/leaves/?status=pending'
    const res = await request.get(url)
    leaveTasks.value = res
  } finally {
    loading.value = false
  }
}

// 审批操作
const handleApprove = (row, result) => {
  const actionText = result === 'approved' ? '同意' : '驳回'
  ElMessageBox.confirm(`确定要${actionText} ${row.student_name} 的请假申请吗？`, '审批确认').then(async () => {
    try {
      // 调用 PATCH 接口更新状态
      await request.patch(`/leaves/${row.id}/`, { status: result })
      ElMessage.success('操作成功')
      fetchLeaveData()
    } catch (e) {
      ElMessage.error('操作失败')
    }
  })
}

// 获取异常考勤数据
const fetchAlerts = async () => {
  try {
    const res = await request.get('/attendance/alerts/')
    alerts.value = res
  } catch (e) { /* 接口未实现则静默 */ }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const logout = () => {
  localStorage.clear()
  router.push('/login')
}

onMounted(() => {
  fetchLeaveData()
  fetchAlerts()
})
</script>

<style scoped>
.t-header { background: #303133; color: #fff; display: flex; justify-content: space-between; align-items: center; }
.t-main { background: #f4f4f5; min-height: calc(100vh - 60px); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.stat-box { display: flex; justify-content: space-around; text-align: center; }
.stat-item .num { font-size: 24px; font-weight: bold; }
.stat-item .num.success { color: #67C23A; }
.stat-item .num.danger { color: #F56C6C; }
.stat-item .lab { font-size: 12px; color: #909399; margin-top: 5px; }
.alert-item { padding: 10px 0; border-bottom: 1px solid #ebeef5; }
.alert-info { font-size: 13px; margin-left: 10px; }
.time { font-size: 11px; color: #c0c4cc; margin-top: 5px; }
</style>