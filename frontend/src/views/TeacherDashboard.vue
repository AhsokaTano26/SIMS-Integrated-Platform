<template>
  <div class="teacher-layout">
    <el-container class="layout-container">
      <el-aside width="240px" class="aside">
        <div class="logo-box">
          <div class="logo-circle">🛡️</div>
          <span class="logo-text">校园请假管理</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          background-color="#1f2937"
          text-color="#9ca3af"
          active-text-color="#ffffff"
          class="el-menu-vertical"
          @select="handleMenuSelect"
        >
          <el-menu-item index="overview">
            <el-icon><DataBoard /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <el-menu-item index="leaves">
            <el-icon><Postcard /></el-icon>
            <span>审批中心</span>
            <div v-if="pendingCount > 0" class="menu-badge">{{ pendingCount }}</div>
          </el-menu-item>
          <el-menu-item index="attendance">
            <el-icon><Warning /></el-icon>
            <span>销假监控</span>
            <div v-if="overdueCount > 0" class="menu-badge danger">{{ overdueCount }}</div>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container class="main-container">
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ menuTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <div class="user-profile">
              <el-avatar :size="32" class="user-avatar" style="background: #4F46E5">教</el-avatar>
              <el-dropdown trigger="click">
                <span class="el-dropdown-link">
                  {{ teacherName }}
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

        <el-main class="main-content">

          <div v-if="activeMenu === 'overview'" class="fade-in">
            <el-row :gutter="24" class="summary-row">
              <el-col :span="8" v-for="(item, index) in statsList" :key="index">
                <div class="stat-card" :class="item.type">
                  <div class="stat-icon-wrapper">
                    <el-icon :size="24"><component :is="item.icon" /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-label">{{ item.lab }}</div>
                    <div class="stat-number">
                      {{ item.num }}
                    </div>
                  </div>
                  <div class="stat-bg-icon">
                    <el-icon><component :is="item.icon" /></el-icon>
                  </div>
                </div>
              </el-col>
            </el-row>

            <el-row :gutter="24" style="margin-top: 24px;">
              <el-col :span="16">
                <el-card class="chart-card" shadow="never">
                  <template #header><span class="card-title">近七日审批动态</span></template>
                  <div ref="trendChartRef" style="height: 350px;"></div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="chart-card" shadow="never">
                  <template #header><span class="card-title">请假原因分布</span></template>
                  <div ref="reasonChartRef" style="height: 350px;"></div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <el-card v-else-if="activeMenu === 'leaves'" class="fade-in content-card" shadow="never">
            <template #header>
              <div class="flex-between">
                <div class="tab-group">
                  <div
                    class="tab-item"
                    :class="{ active: filterStatus === 'pending' }"
                    @click="changeFilter('pending')"
                  >
                    待处理
                    <span class="tab-badge" v-if="pendingCount > 0">{{ pendingCount }}</span>
                  </div>
                  <div
                    class="tab-item"
                    :class="{ active: filterStatus === 'all' }"
                    @click="changeFilter('all')"
                  >
                    全部记录
                  </div>
                </div>
                <el-button type="primary" icon="Refresh" circle @click="fetchLeaveData" />
              </div>
            </template>

            <el-table :data="leaveTasks" v-loading="loading" style="width: 100%" row-class-name="custom-row">
              <el-table-column label="学生信息" width="180">
                <template #default="scope">
                  <div class="student-info">
                    <el-avatar :size="32" shape="square" :src="scope.row.avatarUrl" style="background:#e0e7ff; color:#4f46e5">{{ scope.row.student_name?.[0] }}</el-avatar>
                    <div class="info-text">
                      <span class="name">{{ scope.row.student_name }}</span>
                      <span class="id">学号：{{ scope.row.student_id_display }}</span>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column prop="reason" label="请假事由" min-width="150" show-overflow-tooltip />

              <el-table-column label="请假时间段" width="240">
                <template #default="scope">
                  <div class="time-block">
                    <div class="time-row"><el-icon><Timer /></el-icon> {{ formatDate(scope.row.start_time) }}</div>
                    <div class="time-row to"><el-icon><Right /></el-icon> {{ formatDate(scope.row.end_time) }}</div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="状态" width="120">
                <template #default="scope">
                  <span class="status-badge" :class="scope.row.status">
                    {{ statusMap[scope.row.status].text }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column label="审批/备注" min-width="150" show-overflow-tooltip>
                <template #default="scope">
                  <span v-if="scope.row.comment" class="comment-text">{{ scope.row.comment }}</span>
                  <span v-else class="empty-text">-</span>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="180" fixed="right">
                <template #default="scope">
                  <div v-if="scope.row.status === 'pending'" class="action-group">
                    <el-button type="success" size="small" plain @click="handleApprove(scope.row, 'approved')">通过</el-button>
                    <el-dropdown trigger="click" @command="(cmd) => handleApprove(scope.row, cmd)">
                      <el-button type="info" size="small" plain class="more-btn">
                        更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="returned">↩️ 退回修改</el-dropdown-item>
                          <el-dropdown-item command="rejected" divided style="color: #ef4444">❌ 驳回申请</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                  <div v-else-if="scope.row.status === 'approved' && !scope.row.report_back_time">
                    <span class="text-xs text-warning">待销假</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-card v-else-if="activeMenu === 'attendance'" class="fade-in content-card" shadow="never">
            <template #header>
              <div class="flex-between">
                <div class="title-with-icon">
                  <el-icon color="#ef4444"><WarningFilled /></el-icon>
                  <span>严重逾期名单</span>
                </div>
                <el-tag type="danger" effect="dark" round>共 {{ overdueCount }} 人</el-tag>
              </div>
            </template>

            <el-alert
              v-if="overdueList.length > 0"
              title="以下学生已超过预计返校时间且未进行销假操作，请尽快联系确认安全。"
              type="error"
              :closable="false"
              show-icon
              class="mb-4"
            />
            <el-empty v-else description="暂无逾期记录，学生们都很守时 ~" />

            <el-table v-if="overdueList.length > 0" :data="overdueList" border stripe>
              <el-table-column prop="student_id_display" label="学号" width="100" />
              <el-table-column prop="student_name" label="姓名" width="120" />
              <el-table-column prop="reason" label="原请假理由" show-overflow-tooltip />
              <el-table-column label="应归时间" width="200">
                <template #default="scope">
                  <span class="text-danger font-bold">{{ formatDate(scope.row.end_time) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="当前状态">
                <template #default="scope">
                  <el-tag type="danger" effect="dark">逾期未归</el-tag>
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
import { DataBoard, Postcard, Warning, WarningFilled, ArrowDown, Timer, Right, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '../utils/request'

const router = useRouter()
const activeMenu = ref('overview')
const teacherName = ref(JSON.parse(localStorage.getItem('user_info') || '{}').username || '管理员')

// 核心数据
const loading = ref(false)
const leaveTasks = ref([])
const overdueList = ref([])
const filterStatus = ref('pending')

// 统计数据 (用于 Badge 和 卡片)
const pendingCount = ref(0)
const overdueCount = ref(0)

// 看板卡片配置
const statsList = ref([
  { lab: '待审批', num: 0, icon: 'Postcard', type: 'blue' }, // 对应 pending
  { lab: '休假中', num: 0, icon: 'Timer', type: 'green' },     // 对应 approved (未销假)
  { lab: '严重逾期', num: 0, icon: 'WarningFilled', type: 'red' } // 对应 overdue
])

const statusMap = {
  approved: { text: '已准假', type: 'success' },
  rejected: { text: '已驳回', type: 'danger' },
  pending: { text: '待审批', type: 'info' },
  returned: { text: '已退回', type: 'warning' },
  reported: { text: '已销假', type: 'primary' },
  canceled: { text: '已撤销', type: 'info' }
}

const menuTitle = computed(() => {
  const map = { overview: '数据看板', leaves: '请假审批', attendance: '销假监控' }
  return map[activeMenu.value]
})

// --- 核心：修复数据统计逻辑 ---
const fetchDashboardStats = async () => {
  try {
    // 1. 获取逾期和未销假数据
    const monitorRes = await request.get('/leaves/monitoring/')
    overdueCount.value = monitorRes.overdue_count || 0
    overdueList.value = monitorRes.overdue_list || []

    // 更新看板: "休假中" = unreported_count (已通过但未销假)
    statsList.value[1].num = monitorRes.unreported_count || 0
    // 更新看板: "严重逾期"
    statsList.value[2].num = monitorRes.overdue_count || 0

    // 2. 获取待审批数量 (需要单独查 pending 列表的长度)
    // 注意：为了性能，最好后端有个 /stats 接口，这里我们先取巧查列表
    const pendingRes = await request.get('/leaves/?status=pending')
    pendingCount.value = pendingRes.length || 0
    statsList.value[0].num = pendingRes.length || 0

  } catch (error) {
    console.error("统计数据加载失败", error)
  }
}

// 切换列表过滤器
const changeFilter = (status) => {
  filterStatus.value = status
  fetchLeaveData()
}

// 获取列表数据
const fetchLeaveData = async () => {
  loading.value = true
  try {
    const url = filterStatus.value === 'all' ? '/leaves/' : '/leaves/?status=pending'
    leaveTasks.value = await request.get(url)
    // 每次拉取列表同时也刷新一下统计，保证 Badge 数字准确
    fetchDashboardStats()
  } finally {
    loading.value = false
  }
}

// 审批操作
const handleApprove = (row, resultStatus) => {
  const actionText = { approved: '通过', rejected: '驳回', returned: '退回修改' }[resultStatus]

  ElMessageBox.prompt(`请填写审批意见（可选）`, `确认${actionText}`, {
    confirmButtonText: '提交',
    cancelButtonText: '取消',
    inputType: 'textarea',
    inputPlaceholder: resultStatus === 'returned' ? '请务必说明退回原因...' : '同意，注意安全...'
  }).then(async ({ value }) => {
    await request.patch(`/leaves/${row.id}/approve/`, {
      status: resultStatus,
      comment: value
    })
    ElMessage.success('操作成功')
    fetchLeaveData()
  }).catch(() => {})
}

const handleMenuSelect = (index) => {
  activeMenu.value = index
  if (index === 'leaves') fetchLeaveData()
  else if (index === 'attendance') fetchDashboardStats()
  else if (index === 'overview') {
    fetchDashboardStats()
    nextTick(() => initCharts())
  }
}

const formatDate = (d) => {
  if (!d) return '--'
  const date = new Date(d)
  return `${date.getMonth()+1}-${date.getDate()} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}

const logout = () => {
  localStorage.clear()
  router.push('/login')
}

// 图表初始化
const trendChartRef = ref(null)
const reasonChartRef = ref(null)

const initCharts = () => {
  if (!trendChartRef.value) return
  // 模拟图表数据，实际可接后端
  const chart1 = echarts.init(trendChartRef.value)
  chart1.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'], boundaryGap: false },
    yAxis: { type: 'value' },
    series: [{ data: [3, 5, 2, 8, 4, 1, 2], type: 'line', smooth: true, areaStyle: { opacity: 0.2, color: '#4F46E5' }, lineStyle: { color: '#4F46E5' }, name: '申请数' }]
  })

  const chart2 = echarts.init(reasonChartRef.value)
  chart2.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: false, itemStyle: { borderRadius: 5 }, data: [{ value: 12, name: '事假' }, { value: 5, name: '病假' }, { value: 2, name: '其他' }] }]
  })
}

onMounted(() => {
  fetchDashboardStats() // 页面加载时立即计算数量
  fetchLeaveData()
  nextTick(() => initCharts())
})
</script>

<style scoped>
/* 全局布局变量 */
.teacher-layout { height: 100vh; background: #f3f4f6; font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.layout-container { height: 100%; }

/* 侧边栏 */
.aside { background-color: #111827; display: flex; flex-direction: column; border-right: 1px solid #374151; }
.logo-box { height: 64px; display: flex; align-items: center; justify-content: center; gap: 10px; border-bottom: 1px solid #1f2937; }
.logo-circle { width: 32px; height: 32px; background: #4F46E5; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.logo-text { color: #fff; font-weight: 600; font-size: 16px; letter-spacing: 0.5px; }

/* 菜单 Badge */
.menu-badge { background: #4F46E5; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-left: auto; line-height: 16px; }
.menu-badge.danger { background: #ef4444; }

/* Header */
.header { background: #fff; height: 64px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; }
.user-profile { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 4px 8px; border-radius: 6px; transition: background 0.2s; }
.user-profile:hover { background: #f3f4f6; }
.el-dropdown-link { font-weight: 500; color: #374151; }

/* 统计卡片 (核心美化) */
.stat-card { background: #fff; border-radius: 16px; padding: 24px; display: flex; align-items: center; position: relative; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); transition: transform 0.2s; border: 1px solid #f3f4f6; }
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
.stat-icon-wrapper { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-right: 16px; }
.stat-card.blue .stat-icon-wrapper { background: #eff6ff; color: #3b82f6; }
.stat-card.green .stat-icon-wrapper { background: #ecfdf5; color: #10b981; }
.stat-card.red .stat-icon-wrapper { background: #fef2f2; color: #ef4444; }
.stat-info { z-index: 2; }
.stat-label { color: #6b7280; font-size: 14px; margin-bottom: 4px; }
.stat-number { color: #111827; font-size: 28px; font-weight: 700; line-height: 1; }
.stat-bg-icon { position: absolute; right: -10px; bottom: -10px; font-size: 80px; opacity: 0.05; transform: rotate(-15deg); z-index: 1; pointer-events: none; }

/* 内容区域 */
.main-content { padding: 24px; max-width: 1400px; margin: 0 auto; width: 100%; }
.chart-card { border-radius: 16px; border: none; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.content-card { border-radius: 16px; border: none; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-height: 500px; }

/* 自定义 Tab */
.tab-group { display: flex; background: #f3f4f6; padding: 4px; border-radius: 8px; gap: 4px; }
.tab-item { padding: 6px 16px; font-size: 14px; color: #6b7280; cursor: pointer; border-radius: 6px; transition: all 0.2s; font-weight: 500; display: flex; align-items: center; gap: 6px; }
.tab-item.active { background: #fff; color: #4F46E5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.tab-badge { background: #ef4444; color: white; padding: 0 6px; border-radius: 99px; font-size: 10px; height: 16px; line-height: 16px; }

/* 表格美化 */
.student-info { display: flex; align-items: center; gap: 12px; }
.info-text { display: flex; flex-direction: column; }
.info-text .name { font-weight: 600; color: #1f2937; }
.info-text .id { font-size: 12px; color: #9ca3af; }

.time-block { display: flex; flex-direction: column; gap: 4px; }
.time-row { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #4b5563; background: #f9fafb; padding: 2px 8px; border-radius: 4px; width: fit-content; }
.time-row.to { color: #6b7280; }

/* 状态 Badge 自定义 */
.status-badge { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; }
.status-badge.pending { background: #eff6ff; color: #3b82f6; }
.status-badge.approved { background: #ecfdf5; color: #059669; }
.status-badge.rejected { background: #fef2f2; color: #dc2626; }
.status-badge.returned { background: #fffbeb; color: #d97706; }
.status-badge.reported { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; }

/* 动画 */
.fade-in { animation: fadeInUp 0.5s ease-out; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* 通用 Flex */
.flex-between { display: flex; justify-content: space-between; align-items: center; }
.text-danger { color: #ef4444; }
.text-xs { font-size: 12px; }
.mb-4 { margin-bottom: 16px; }
</style>