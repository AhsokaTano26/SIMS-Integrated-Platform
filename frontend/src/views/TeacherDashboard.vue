<template>
  <div class="teacher-layout">
    <el-container class="layout-container">
      <el-aside width="240px" class="aside">
        <div class="logo-box">
          <div class="logo-circle">
            <el-icon><Management /></el-icon>
          </div>
          <span class="logo-text">智慧管理教师端</span>
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
          <el-menu-item index="holiday">
            <el-icon><Warning /></el-icon>
            <span>销假监控</span>
            <div v-if="overdueCount > 0" class="menu-badge danger">{{ overdueCount }}</div>
          </el-menu-item>
          <el-menu-item index="attendance">
            <el-icon><Position /></el-icon>
            <span>打卡管理</span>
            <div v-if="overdueCount > 0" class="menu-badge danger">{{ attendanceStats[3]["value"] }}</div>
          </el-menu-item>
          <el-menu-item index="personal">
            <el-icon><House /></el-icon>
            <span>个人信息</span>
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
              <el-dropdown trigger="click">
                <el-avatar :src="getFullAvatarUrl(teacherInfo.avatar_url)">
                  {{ teacherInfo.username?.charAt(0) }}
                </el-avatar>
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
              <el-table-column prop="leave_for" label="前往地点" min-width="150" show-overflow-tooltip />

              <el-table-column label="请假时间段" width="150">
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
                    <el-dropdown trigger="click" @command="(cmd) => handleApprove(scope.row, cmd)">
                      <el-button type="info" size="small" plain class="more-btn">
                        处理<el-icon class="el-icon--right"><arrow-down /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="approved">通过申请</el-dropdown-item>
                          <el-dropdown-item command="returned">退回修改</el-dropdown-item>
                          <el-dropdown-item command="rejected" divided style="color: #ef4444">驳回申请</el-dropdown-item>
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

          <el-card v-else-if="activeMenu === 'holiday'" class="fade-in content-card" shadow="never">
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
            <el-empty v-else description="暂无逾期记录" />

            <el-table v-if="overdueList.length > 0" :data="overdueList" border stripe>
              <el-table-column prop="student_id_display" label="学号" width="100" />
              <el-table-column prop="student_name" label="姓名" width="120" />
              <el-table-column prop="reason" label="请假理由" show-overflow-tooltip />
              <el-table-column prop="leave_for" label="前往地点" show-overflow-tooltip />
              <el-table-column label="应归时间" width="200">
                <template #default="scope">
                  <span class="text-danger font-bold">{{ formatDate(scope.row.end_time) }}</span>
                </template>
              </el-table-column>
                <el-table-column label="当前状态">
                  <template #default="scope">
                    <el-button type="danger" effect="dark" @click="handleClick(scope.row)">
                      逾期未归
                    </el-button>
                  </template>
                </el-table-column>
            </el-table>
          </el-card>

          <el-card v-else-if="activeMenu === 'attendance'" class="fade-in content-card" shadow="never">
            <el-tabs v-model="attendanceTab">
              <el-tab-pane label="实时监控" name="monitor">
  <div class="mb-4" style="display: flex; align-items: center; gap: 10px;">
    <span>当前监控任务：</span>
    <el-select
      v-model="currentMonitorId"
      placeholder="请选择查寝任务"
      style="width: 280px"
      @change="handleMonitorTaskChange"
    >
      <el-option
        v-for="item in taskList"
        :key="item.config_id"
        :label="`${item.config_name} (${item.check_date})`"
        :value="item.config_id"
      />
    </el-select>

    <el-tag v-if="currentMonitorId" type="info" effect="plain">
       {{ taskList.find(t => t.config_id === currentMonitorId)?.status_desc }}
    </el-tag>
  </div>

  <el-row :gutter="20" class="mb-6">
    <el-col :span="6" v-for="stat in attendanceStats" :key="stat.label">
      <div class="stat-mini-card" :class="stat.type">
        <div class="label">{{ stat.label }}</div>
        <div class="value">{{ stat.value }} <span class="unit">人</span></div>
      </div>
    </el-col>
  </el-row>

  <div class="flex-between mb-4">
    <div class="title-with-icon">
      <el-icon color="#ef4444"><WarningFilled /></el-icon>
      <span class="font-bold">异常名单 (缺勤/晚归)</span>
    </div>
    <el-button type="primary" size="small" plain icon="Bell">一键提醒</el-button>
  </div>

  <el-table :data="abnormalList" border stripe style="width: 100%">
    <el-table-column prop="student_name" label="姓名" width="120" />
    <el-table-column prop="student_id" label="学号" width="140" />
    <el-table-column prop="last_location" label="状态描述" show-overflow-tooltip />
    <el-table-column prop="status" label="异常类型">
      <template #default="scope">
        <el-tag :type="scope.row.status === 'late' ? 'warning' : 'danger'">
          {{ scope.row.status === 'late' ? '晚归' : '缺勤' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="120">
      <template #default="scope">
        <el-button link type="primary">联系学生</el-button>
      </template>
    </el-table-column>
  </el-table>
</el-tab-pane>

<el-tab-pane label="打卡任务管理" name="tasks">
  <div class="flex-between mb-4">
    <el-button type="primary" icon="Plus" @click="showCreateTask = true">发布新查寝</el-button>
    <el-radio-group v-model="taskFilter" size="small">
      <el-radio-button label="active">进行中</el-radio-button>
      <el-radio-button label="all">全部任务</el-radio-button>
    </el-radio-group>
  </div>

  <el-table :data="taskList" style="width: 100%">
    <el-table-column prop="config_name" label="任务名称" min-width="120" />

    <el-table-column label="起止时间 (东八区)" min-width="240">
      <template #default="scope">
        <div style="font-size: 13px; line-height: 1.5;">
          <div><el-tag size="small">始</el-tag> {{ scope.row.normal_start }}</div>
          <div><el-tag size="small" type="danger">终</el-tag> {{ scope.row.normal_end }}</div>
        </div>
      </template>
    </el-table-column>

    <el-table-column label="晚归截止" min-width="180">
      <template #default="scope">
        <span v-if="scope.row.late_end" style="font-size: 13px; color: #e6a23c;">
           {{ scope.row.late_end }}
        </span>
        <span v-else>--</span>
      </template>
    </el-table-column>

    <el-table-column label="状态" width="100">
      <template #default="scope">
        <el-tag :type="scope.row.status === 'in_progress' ? 'success' : 'info'">
          {{ scope.row.status_desc }}
        </el-tag>
      </template>
    </el-table-column>

    <el-table-column label="操作" width="120">
      <template #default="scope">
        <el-button link type="primary" @click="handleMonitorTaskChange(scope.row.config_id); attendanceTab='monitor'">
          查看统计
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</el-tab-pane>
            </el-tabs>

<el-dialog v-model="showCreateTask" title="发布新查寝任务" width="500px">
  <el-form :model="taskForm" label-position="top">
    <el-form-item label="任务标题">
      <el-input v-model="taskForm.title" placeholder="如：1月11日全员晚点名" />
    </el-form-item>

    <el-form-item label="正常打卡时间范围 (日期+时间)">
      <el-date-picker
        v-model="taskForm.timeRange"
        type="datetimerange"
        range-separator="至"
        start-placeholder="开始时间"
        end-placeholder="结束时间"
        format="YYYY-MM-DD HH:mm"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="晚归截止时间 (可选)">
      <el-date-picker
        v-model="taskForm.lateTime"
        type="datetime"
        placeholder="超过正常结束时间后的最终截止点"
        format="YYYY-MM-DD HH:mm"
        style="width: 100%"
      />
    </el-form-item>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="打卡半径 (米)">
          <el-input-number v-model="taskForm.radius" :min="100" :step="100" style="width: 100%" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
         <el-form-item label="需要照片">
            <el-switch v-model="taskForm.needMaterial" />
         </el-form-item>
      </el-col>
    </el-row>
  </el-form>
  <template #footer>
    <el-button @click="showCreateTask = false">取消</el-button>
    <el-button type="primary" @click="submitTask">立即发布</el-button>
  </template>
</el-dialog>
          </el-card>


            <el-card v-else-if="activeMenu === 'personal'" class="fade-in content-card personal-container" shadow="never">
            <el-row :gutter="40">
              <el-col :span="8">
                <div class="profile-sidebar">
                  <div class="avatar-upload">
                    <el-avatar :size="100" :src="getFullAvatarUrl(teacherInfo.avatar_url)" style="background: #4F46E5; font-size: 40px;">
                        {{ teacherInfo.username?.[0] }}
                    </el-avatar>
                    <div class="teacher-name-tag">
                      <h2>{{ teacherInfo.username }}</h2>
                      <el-tag size="small" effect="plain">{{ eduLevelMap[teacherInfo.role] || '任课教师' }}</el-tag>
                    </div>
                  </div>

                  <div class="personal-stats">
                    <div class="p-stat-item">
                      <span class="p-stat-val">{{ pendingCount }}</span>
                      <span class="p-stat-lab">待我审批</span>
                    </div>
                    <el-divider direction="vertical" />
                    <div class="p-stat-item">
                      <span class="p-stat-val">{{ overdueCount }}</span>
                      <span class="p-stat-lab">请假逾期</span>
                    </div>
                    <el-divider direction="vertical" />
                    <div class="p-stat-item">
                      <span class="p-stat-val">{{ attendanceStats[3]["value"] }}</span>
                      <span class="p-stat-lab">打卡异常</span>
                    </div>
                  </div>

                  <el-divider />

                  <div class="info-list">
                    <div class="info-item">
                      <el-icon><Postcard /></el-icon>
                      <span class="label">教工号：</span>
                      <span class="value">{{ teacherInfo.student_id || '2024001' }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><School /></el-icon>
                      <span class="label">所属部门：</span>
                      <span class="value">{{ teacherInfo.major || '学生工作处' }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><OfficeBuilding /></el-icon>
                      <span class="label">所属学院：</span>
                      <span class="value">{{ teacherInfo.college || '未知' }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><Message /></el-icon>
                      <span class="label">联系邮箱：</span>
                      <span class="value">{{ teacherInfo.email || '未绑定' }}</span>
                    </div>
                  </div>
                </div>
              </el-col>

              <el-col :span="16">
                <el-tabs v-model="personalActiveTab">
                  <el-tab-pane label="基本设置" name="info">
                    <el-form :model="teacherInfo" label-position="top" class="personal-form">
                      <el-row :gutter="20">
                        <el-col :span="12">
                          <el-form-item label="姓名">
                            <el-input v-model="teacherInfo.username" />
                          </el-form-item>
                        </el-col>
                        <el-col :span="12">
                          <el-form-item label="手机号码">
                            <el-input v-model="teacherInfo.phone" />
                          </el-form-item>
                        </el-col>
                      </el-row>

                      <el-row :gutter="20">
                        <el-col :span="12">
                          <el-form-item label="所属学院">
                            <el-input v-model="teacherInfo.college" placeholder="例如：信息工程学院" />
                          </el-form-item>
                        </el-col>
                        <el-col :span="12">
                          <el-form-item label="部门名称">
                            <el-input v-model="teacherInfo.major" placeholder="例如：网络安全" />
                          </el-form-item>
                        </el-col>
                      </el-row>

                      <el-row :gutter="20">
                        <el-col :span="12">
                          <el-form-item label="性别">
                            <el-select v-model="teacherInfo.gender" style="width: 100%">
                              <el-option label="男" value="male" />
                              <el-option label="女" value="female" />
                            </el-select>
                          </el-form-item>
                        </el-col>
                      </el-row>

                      <el-button type="primary" @click="updateProfile" :loading="loading">保存更改</el-button>
                    </el-form>
                  </el-tab-pane>

                  <el-tab-pane label="安全设置" name="security">
                    <div class="security-list">
                      <div class="security-item">
                        <div class="sec-info">
                          <div class="sec-title">账户密码</div>
                          <div class="sec-desc">定期更换密码可以保护您的账号安全</div>
                        </div>
                        <el-button link type="primary" @click="handleChangePassword">重置密码</el-button>
                      </div>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </el-col>
            </el-row>
          </el-card>

          <el-dialog
            v-model="detailVisible"
            title="逾期学生详细档案"
            width="500px"
            center
            destroy-on-close
          >
            <div v-if="currentStudent" class="student-detail-modal">
              <div class="detail-header">
                <el-avatar :size="64" style="background: #fef2f2; color: #ef4444; font-size: 24px;">
                  {{ currentStudent.student_name?.[0] }}
                </el-avatar>
                <h3>{{ currentStudent.student_name }}</h3>
                <el-tag type="danger">学号：{{ currentStudent.student_id_display }}</el-tag>
              </div>

              <el-descriptions :column="1" border class="mt-4">
                <el-descriptions-item label="请假事由">{{ currentStudent.reason }}</el-descriptions-item>
                <el-descriptions-item label="前往地点">{{ currentStudent.leave_for }}</el-descriptions-item>
                <el-descriptions-item label="离校时间">{{ formatDate(currentStudent.start_time) }}</el-descriptions-item>
                <el-descriptions-item label="应归时间">
                  <span style="color: #ef4444; font-weight: bold;">{{ formatDate(currentStudent.end_time) }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="联系电话">
                  {{ studentDetail.phone || '未录入' }}
                </el-descriptions-item>
                <el-descriptions-item label="学院专业班级">
                  {{ studentDetail.college || '未录入' }}{{ studentDetail.grade || '未录入' }}{{ studentDetail.major || '未录入' }}{{ studentDetail.class_name || '未录入' }}
                </el-descriptions-item>
                <el-descriptions-item label="寝室地址">
                  {{ studentDetail.address || '未录入' }}
                </el-descriptions-item>
              </el-descriptions>

              <div class="detail-footer">
                <el-button @click="detailVisible = false">关闭窗口</el-button>
              </div>
            </div>
          </el-dialog>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DataBoard,
  OfficeBuilding,
  Postcard,
  Warning,
  WarningFilled,
  ArrowDown,
  Timer,
  Right,
  Refresh,
  Message,
  Management, Position, House, Comment, School
} from '@element-plus/icons-vue'
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
const detailVisible = ref(false)
const currentStudent = ref(null)

// 个人中心逻辑
const personalActiveTab = ref('info')
// 1. 初始化响应式数据，字段名与 API 返回的 JSON 保持一致
const teacherInfo = ref({
  id: null,
  username: "",
  college: "",
  major: "",
  phone: "",
  education_level: "",
  gender: "",
  address: "",
  dorm_type: "",
  dormitory: "",
  avatar_url: "",
});

// 2. 映射显示文字（例如培养层次从英文转中文）
const eduLevelMap = {
  'undergraduate': '本科生',
  'master': '研究生',
  'doctor': '博士生',
  'other': '其他',
  "teacher": '教师',
};

// 3. 获取数据的函数
const fetchProfile = async () => {
  try {
    // 接入你提供的 API
    const res = await request.get('/auth/users/me/');
    teacherInfo.value = res;
    console.log("后端返回的用户信息:", teacherInfo.value);

    // 同步更新顶部 Header 显示的名字
    teacherName.value = res.username;
    // 可选：更新缓存
    localStorage.setItem('user_info', JSON.stringify(res));
  } catch (error) {
    console.error("获取个人信息失败:", error);
    ElMessage.error("用户信息加载失败");
  }
};
const updateProfile = async () => {
  if (!teacherInfo.value.id) {
    ElMessage.error("用户信息不完整");
    return;
  }

  try {
    // 1. 定义所有可能修改的字段
    const fields = [
      'username', 'phone', 'college', 'major',
      'education_level', 'gender', 'address'
    ];

    // 2. 动态构造 payload：只包含有值的字段
    const payload = {};
    fields.forEach(field => {
      const value = teacherInfo.value[field];
      // 只有当值不为 null, undefined 且不是空字符串时才放入 payload
      if (value !== null && value !== undefined && value !== '') {
        payload[field] = value;
      }
    });

    // 3. 发送请求
    await request.patch(`/auth/users/${teacherInfo.value.id}/`, payload);

    ElMessage.success('个人资料更新成功');

    // 更新本地同步
    const localUser = JSON.parse(localStorage.getItem('user_info') || '{}');
    localStorage.setItem('user_info', JSON.stringify({ ...localUser, ...payload }));
    teacherName.value = teacherInfo.value.username;

  } catch (error) {
    console.error("更新失败:", error);
    // 提取后端的具体报错信息
    const errorMsg = error.response?.data?.address?.[0] ||
                     error.response?.data?.detail ||
                     "更新失败，请稍后再试";
    ElMessage.error(errorMsg);
  }
};

const handleChangePassword = () => {
  ElMessageBox.prompt('请输入新密码', '修改密码', {
    confirmButtonText: '提交',
    cancelButtonText: '取消',
    inputType: 'password'
  }).then(() => {
    ElMessage.success('密码修改成功，请下次登录时使用新密码')
  })
}


//学生信息
// 存放从 /api/auth/users/{id}/ 获取的详细学生资料
const studentDetail = ref({
  username: '',
  student_id: '',
  college: '',
  major: '',
  class_name: '',
  phone: '',
  dorm_type: '',
  dormitory: '',
  avatar: ''
});


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
  const map = { overview: '数据看板', leaves: '请假审批', holiday: '销假监控' }
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

  ElMessageBox.prompt(`请填写审批意见`, `确认${actionText}`, {
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
  if (index === 'leaves') {
    fetchLeaveData()
  } else if (index === 'holiday') {
    fetchDashboardStats()
  } else if (index === 'personal') {
    // 关键补全：点击个人中心菜单时拉取后端数据
    fetchProfile()
  } else if (index === 'overview') {
    fetchDashboardStats()
    nextTick(() => initCharts())
  }
}

const formatDate = (d) => {
  if (!d) return '--'
  const date = new Date(d)
  return `${date.getMonth()+1}-${date.getDate()} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}

const getFullAvatarUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const baseUrl = `http://127.0.0.1:8000${url}`
  return `${baseUrl}?t=${new Date().getTime()}`
}

const logout = () => {
  localStorage.clear()
  router.push('/login')
}

// 图表初始化
const trendChartRef = ref(null)
const reasonChartRef = ref(null)
const handleClick = async (row) => {
  currentStudent.value = row; // 保存右图的请假记录数据

  try {
    // 1. 使用右图中的 student 字段（即用户ID，例如图中的 8）调用接口
    // 注意：请根据你实际的请求工具调整路径
    const res = await request.get(`/auth/users/${row.student}/`);

    // 2. 将左图结构的数据存入 studentDetail
    studentDetail.value = res;

    // 3. 数据加载完成后打开弹窗
    detailVisible.value = true;
  } catch (error) {
    ElMessage.error("获取学生详细档案失败");
    console.error(error);
  }
};
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

//打卡模块
const attendanceTab = ref('monitor')
const showCreateTask = ref(false)
const taskFilter = ref('all')

// 1. 核心数据容器
const taskList = ref([])
const currentMonitorId = ref(null)
const attendanceStats = ref([
  { label: '应到人数', value: 0, type: 'info' },
  { label: '正常签到', value: 0, type: 'success' },
  { label: '晚归人员', value: 0, type: 'warning' },
  { label: '缺勤/异常', value: 0, type: 'danger' }
])
const abnormalList = ref([])

// 2. 表单数据
// 修改点：timeRange 默认为空数组，等待用户选择日期+时间
const taskForm = ref({
  title: '',
  timeRange: [], // [Date, Date]
  radius: 500,
  lateTime: null, // Date
  needMaterial: false
})

// ---------------------- 工具函数 ----------------------

// 核心修改：手动格式化时间，确保发送给后端的是 "YYYY-MM-DD HH:mm"
// 使用 getHours() 获取本地时间（东八区），避免 toISOString() 转成 UTC
const formatDateStr = (date) => {
  if (!date) return null
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}`
}

// ---------------------- API 交互方法 ----------------------

// 3. 获取查寝任务列表 (GET /api/dorm_check/config/)
const fetchAttendanceTasks = async () => {
  try {
    // 接口地址更新
    const res = await request.get('/dorm_check/config/')
    taskList.value = res

    // 如果有任务且当前无选中，默认选中第一个（通常是最新的）
    if (res.length > 0 && !currentMonitorId.value) {
      currentMonitorId.value = res[0].config_id
      fetchTaskStats(res[0].config_id)
    }
  } catch (error) {
    console.error("获取任务列表失败", error)
  }
}

// 4. 获取特定任务的统计数据 (GET /api/dorm_check/statistics)
const fetchTaskStats = async (configId) => {
  if (!configId) return
  try {
    const res = await request.get('/dorm_check/statistics', {
      params: { check_config_id: configId }
    })

    const stats = res.statistics
    const lists = res.lists

    attendanceStats.value = [
      { label: '应到人数', value: stats.total, type: 'info' },
      { label: '正常签到', value: stats.normal, type: 'success' },
      { label: '晚归人员', value: stats.late, type: 'warning' },
      { label: '缺勤/异常', value: stats.absent, type: 'danger' }
    ]

    const lateList = lists.late.map(item => ({
      student_name: item.name,
      student_id: item.id || '未知',
      last_location: '已打卡(晚归)',
      status: 'late',
      check_time: item.time,
      reason: item.reason
    }))

    const absentList = lists.absent.map(item => ({
      student_name: item.name,
      student_id: item.id,
      last_location: '无记录',
      status: 'absent',
      check_time: '--',
      reason: '未打卡'
    }))

    abnormalList.value = [...absentList, ...lateList]

  } catch (error) {
    console.error("获取统计失败", error)
    ElMessage.error("统计数据加载失败")
  }
}

// 5. 提交新任务 (POST /api/dorm_check/config/)
const submitTask = async () => {
  // 校验：必须选择时间范围
  if (!taskForm.value.title || !taskForm.value.timeRange || taskForm.value.timeRange.length < 2) {
    ElMessage.warning('请补全任务信息（标题及起止时间）')
    return
  }

  const payload = {
    config_name: taskForm.value.title,
    // 使用自定义格式化函数，转为 "2026-01-11 21:00" 格式
    normal_start: formatDateStr(taskForm.value.timeRange[0]),
    normal_end: formatDateStr(taskForm.value.timeRange[1]),
    // 晚归时间可选
    late_end: taskForm.value.lateTime ? formatDateStr(taskForm.value.lateTime) : null,
    valid_range: taskForm.value.radius,
    need_material: taskForm.value.needMaterial
  }

  try {
    // 接口地址更新
    await request.post('/dorm_check/config/', payload)
    ElMessage.success('查寝任务发布成功')
    showCreateTask.value = false
    // 重置表单
    taskForm.value.title = ''
    taskForm.value.timeRange = []
    taskForm.value.lateTime = null
    // 刷新列表
    fetchAttendanceTasks()
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || '发布失败')
  }
}

const handleMonitorTaskChange = (val) => {
    currentMonitorId.value = val
    fetchTaskStats(val)
}

onMounted(() => {
  fetchProfile()
  fetchDashboardStats()
  fetchLeaveData()
  fetchAttendanceTasks()
  nextTick(() => initCharts())
})



onMounted(() => {
  fetchProfile()
  fetchDashboardStats()
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
.student-detail-modal {
  padding: 10px;
}
.detail-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.detail-header h3 {
  margin: 0;
  font-size: 20px;
  color: #1f2937;
}
.mt-4 {
  margin-top: 16px;
}
.detail-footer {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 12px;
}
/* 个人中心样式 */
.personal-container {
  padding: 40px !important;
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1px solid #f3f4f6;
  padding-right: 20px;
}

.teacher-name-tag {
  text-align: center;
  margin-top: 16px;
}

.teacher-name-tag h2 {
  margin: 0 0 8px 0;
  color: #111827;
}

.personal-stats {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
  margin-top: 24px;
}

.p-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.p-stat-val {
  font-size: 20px;
  font-weight: 700;
  color: #4F46E5;
}

.p-stat-lab {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.info-list {
  width: 100%;
  margin-top: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  color: #4b5563;
  font-size: 14px;
}

.info-item .el-icon {
  color: #9ca3af;
}

.info-item .label {
  color: #9ca3af;
  width: 70px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid #f3f4f6;
}

.sec-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.sec-desc {
  font-size: 13px;
  color: #9ca3af;
}

.personal-form {
  margin-top: 20px;
  max-width: 600px;
}
.stat-mini-card {
  padding: 20px;
  border-radius: 12px;
  background: #f8fafc;
  border-left: 4px solid #e2e8f0;
}
.stat-mini-card.success { border-left-color: #10b981; background: #ecfdf5; }
.stat-mini-card.danger { border-left-color: #ef4444; background: #fef2f2; }
.stat-mini-card.warning { border-left-color: #f59e0b; background: #fffbeb; }
.stat-mini-card .label { font-size: 13px; color: #64748b; margin-bottom: 8px; }
.stat-mini-card .value { font-size: 24px; font-weight: bold; color: #1e293b; }
.stat-mini-card .unit { font-size: 12px; font-weight: normal; color: #94a3b8; }
.mb-6 { margin-bottom: 24px; }
</style>