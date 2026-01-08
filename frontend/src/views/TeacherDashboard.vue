<template>
  <div class="teacher-layout">
    <el-container class="layout-container">
      <el-aside width="220px" class="aside">
        <div class="logo-box">
          <span class="logo-icon">🛡️</span>
          <span class="logo-text">管理系统教师端</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          class="el-menu-vertical"
          @select="handleMenuSelect"
        >
          <el-menu-item index="overview">
            <el-icon><DataBoard /></el-icon>
            <span>数据看板</span>
          </el-menu-item>
          <el-menu-item index="leaves">
            <el-icon><Postcard /></el-icon>
            <span>请假审批单</span>
          </el-menu-item>
          <el-menu-item index="attendance">
            <el-icon><Warning /></el-icon>
            <span>异常预警</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="breadcrumb">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>控制台</el-breadcrumb-item>
              <el-breadcrumb-item>{{ menuTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="user-info">
            <el-dropdown>
              <span class="el-dropdown-link">
                <el-avatar :size="24" style="margin-right: 8px">教</el-avatar>
                {{ teacherName }} 老师
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main class="main-content">

          <div v-if="activeMenu === 'overview'" class="fade-in">
            <el-row :gutter="20" class="summary-row">
              <el-col :span="8" v-for="item in statsList" :key="item.lab">
                <el-card shadow="hover" class="stat-card">
                  <div class="stat-body">
                    <div class="stat-icon" :style="{ background: item.color + '22' }">
                      <el-icon :size="28" :color="item.color"><component :is="item.icon" /></el-icon>
                    </div>
                    <div class="stat-info">
                      <div class="stat-lab">{{ item.lab }}</div>
                      <div class="stat-num">{{ item.num }}</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="10">
                <el-card header="请假原因构成" shadow="never">
                  <div ref="reasonChartRef" style="height: 320px;"></div>
                </el-card>
              </el-col>
              <el-col :span="14">
                <el-card header="近一周异常打卡趋势" shadow="never">
                  <div ref="trendChartRef" style="height: 320px;"></div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <el-card v-else-if="activeMenu === 'leaves'" class="fade-in" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="title">待办审批流程</span>
                <el-radio-group v-model="filterStatus" size="small" @change="fetchLeaveData">
                  <el-radio-button label="pending">待处理</el-radio-button>
                  <el-radio-button label="all">全部记录</el-radio-button>
                </el-radio-group>
              </div>
            </template>

            <el-table :data="leaveTasks" v-loading="loading" stripe style="width: 100%">
              <el-table-column prop="student_name" label="学生" width="100" />
              <el-table-column prop="reason" label="请假理由" show-overflow-tooltip />
              <el-table-column label="起止时间" width="260">
                <template #default="scope">
                  {{ formatDate(scope.row.start_time) }} ~ {{ formatDate(scope.row.end_time) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="scope">
                  <div class="table-ops" v-if="scope.row.status === 'pending'">
                    <el-button type="success" size="small" link @click="handleApprove(scope.row, 'approved')">同意</el-button>
                    <el-button type="danger" size="small" link @click="handleApprove(scope.row, 'rejected')">驳回</el-button>
                  </div>
                  <el-tag v-else :type="statusMap[scope.row.status].type" size="small">
                    {{ statusMap[scope.row.status].text }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-card v-else-if="activeMenu === 'attendance'" class="fade-in" shadow="never">
            <template #header><span class="title">今日异常打卡名单</span></template>
            <el-table :data="alerts" stripe>
              <el-table-column prop="student" label="学生姓名" />
              <el-table-column prop="distance" label="偏离距离(米)">
                <template #default="scope">
                  <span style="color: #f56c6c; font-weight: bold;">{{ scope.row.distance }}m</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="打卡时间">
                <template #default="scope">{{ formatDate(scope.row.time) }}</template>
              </el-table-column>
              <el-table-column label="状态">
                <template #default="scope">
                  <el-tag type="danger" effect="plain">位置异常</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataBoard, Postcard, Warning, ArrowDown, UserFilled, CircleCheck } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '../utils/request'

const router = useRouter()
const activeMenu = ref('overview')
const teacherName = ref(JSON.parse(localStorage.getItem('user_info') || '{}').username)

// 图表 DOM 引用
const reasonChartRef = ref(null)
const trendChartRef = ref(null)

const menuTitle = computed(() => {
  const map = { overview: '数据看板', leaves: '请假审批', attendance: '考勤预警' }
  return map[activeMenu.value]
})

const statsList = ref([
  { lab: '管理总人数', num: 120, icon: 'UserFilled', color: '#409EFF' },
  { lab: '今日已打卡', num: 116, icon: 'CircleCheck', color: '#67C23A' },
  { lab: '当前异常', num: 4, icon: 'Warning', color: '#F56C6C' }
])

const statusMap = {
  approved: { text: '已准假', type: 'success' },
  rejected: { text: '已驳回', type: 'danger' },
  pending: { text: '待处理', type: 'info' }
}

const leaveTasks = ref([])
const alerts = ref([])
const loading = ref(false)
const filterStatus = ref('pending')

// 菜单切换逻辑
const handleMenuSelect = (index) => {
  activeMenu.value = index
  if (index === 'overview') nextTick(() => initCharts())
  else if (index === 'leaves') fetchLeaveData()
  else if (index === 'attendance') fetchAlerts()
}

// 初始化 ECharts
const initCharts = async () => {
  try {
    const res = await request.get('/statistics/')

    // 摘要数据更新
    statsList.value[0].num = res.total_count || 120
    statsList.value[1].num = res.normal_count || 116
    statsList.value[2].num = res.abnormal_count || 4

    const rChart = echarts.init(reasonChartRef.value)
    rChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%', left: 'center' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8 },
        label: { show: false },
        data: res.reasons
      }]
    })

    const tChart = echarts.init(trendChartRef.value)
    tChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: res.trend.map(d => d.date), boundaryGap: false },
      yAxis: { type: 'value' },
      series: [{
        name: '异常人数',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3, color: '#f56c6c' },
        lineStyle: { color: '#f56c6c' },
        data: res.trend.map(d => d.count)
      }]
    })
  } catch (e) { console.error("统计加载失败") }
}

const fetchLeaveData = async () => {
  loading.value = true
  try {
    const url = filterStatus.value === 'all' ? '/leaves/' : '/leaves/?status=pending'
    leaveTasks.value = await request.get(url)
  } finally { loading.value = false }
}

const fetchAlerts = async () => {
  alerts.value = await request.get('/attendance/alerts/')
}

const handleApprove = (row, result) => {
  ElMessageBox.confirm(`确认执行此审批操作吗？`, '提示').then(async () => {
    await request.patch(`/leaves/${row.id}/`, { status: result })
    ElMessage.success('审批成功')
    fetchLeaveData()
  })
}

const formatDate = (d) => d ?
  new Date(d).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false // 建议加上，强制24小时制
  }).replace(/\//g, '-') : '-'; // 将斜杠替换为横杠

const logout = () => {
  localStorage.clear()
  router.push('/login')
}

onMounted(() => {
  fetchLeaveData()
  fetchAlerts()
  nextTick(() => initCharts())
})
</script>

<style scoped>
.teacher-layout { height: 100vh; background: #f0f2f5; }
.layout-container { height: 100%; }

/* 侧边栏样式 */
.aside { background-color: #304156; color: #fff; box-shadow: 2px 0 6px rgba(0,21,41,.35); }
.logo-box { height: 60px; line-height: 60px; text-align: center; background: #2b2f3a; color: #409EFF; font-weight: bold; font-size: 18px; }

/* 头部样式 */
.header { background: #fff; height: 60px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 1px solid #e6e6e6; }
.el-dropdown-link { cursor: pointer; display: flex; align-items: center; color: #606266; }

/* 主体内容 */
.main-content { padding: 20px; }
.summary-row { margin-bottom: 20px; }

.stat-card { border: none; border-radius: 8px; }
.stat-body { display: flex; align-items: center; gap: 20px; }
.stat-icon { width: 60px; height: 60px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-lab { color: #909399; font-size: 14px; }
.stat-num { font-size: 28px; font-weight: bold; color: #303133; }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.title { font-weight: bold; color: #333; }

.table-ops { display: flex; gap: 10px; }

.fade-in { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>