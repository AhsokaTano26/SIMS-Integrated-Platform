<template>
  <div class="dashboard">
    <el-header class="header">
      <span>学生事务中心</span>
      <el-button type="danger" size="small" @click="logout">退出登录</el-button>
    </el-header>

    <el-main>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>📍 智能查寝打卡</template>
            <div class="checkin-box">
              <el-button type="primary" :loading="loading" @click="handleCheckIn">
                立即定位并打卡
              </el-button>
              <p v-if="locationTip" class="tip">{{ locationTip }}</p>
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>📝 我的请假</template>
            <el-empty description="暂无申请记录" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import request from '../utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();
const loading = ref(false);
const locationTip = ref('');

const handleCheckIn = () => {
  loading.value = true;
  if (!navigator.geolocation) {
    ElMessage.error('浏览器不支持定位');
    loading.value = false;
    return;
  }

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    locationTip.value = `当前坐标: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;

    try {
      const res = await request.post('/attendance/', { lat: latitude, lng: longitude });
      if (res.is_normal) {
        ElMessageBox.alert(`打卡成功！距离宿舍 ${res.distance} 米`, '系统提示', { type: 'success' });
      } else {
        ElMessageBox.alert(`打卡异常！你不在宿舍范围内（距离 ${res.distance} 米）`, '警告', { type: 'warning' });
      }
    } finally {
      loading.value = false;
    }
  }, (err) => {
    ElMessage.error('定位失败，请确保开启位置权限');
    loading.value = false;
  });
};

const logout = () => {
  localStorage.clear();
  router.push('/login');
};
</script>

<style scoped>
.header { background: #409EFF; color: white; display: flex; justify-content: space-between; align-items: center; }
.checkin-box { text-align: center; padding: 20px; }
.tip { font-size: 12px; color: #999; margin-top: 10px; }
</style>