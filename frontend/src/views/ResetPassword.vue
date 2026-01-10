<template>
  <div class="reset-container">
    <el-card class="reset-box">
      <template #header>
        <div class="card-header">
          <span>找回密码</span>
        </div>
      </template>

      <div class="info-content">
        <el-result
          icon="warning"
          title="找回密码说明"
          sub-title="本系统目前不支持自助找回密码"
        >
          <template #extra>
            <div class="admin-notice">
              <p>为了您的账号安全，重置密码请联系系统管理员进行人工核验。</p>

              <el-descriptions :column="0" border direction="vertical" :size="5" class="admin-details">
                <el-descriptions-item label="管理部门">信息技术中心</el-descriptions-item>
                <el-descriptions-item label="服务热线">010-12345678</el-descriptions-item>
                <el-descriptions-item label="官方邮箱">support@cqu.edu.cn</el-descriptions-item>
                <el-descriptions-item label="办公地址">重庆大学科学城校区虎溪校园信息科研楼B831</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
        </el-result>
      </div>

      <div class="footer-action">
        <el-button type="primary" plain @click="$router.push('/login')">
          返回登录页面
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>

import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.reset-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.reset-box {
  width: 480px;
  border-radius: 8px;
}

.card-header {
  font-weight: bold;
  font-size: 18px;
}

.admin-notice {
  text-align: left;
  color: #606266;
  font-size: 14px;
}

.admin-details {
  margin-top: 15px;
}

.footer-action {
  margin-top: 20px;
  text-align: center;
}

:deep(.el-result__extra) {
  width: 100%;
}
</style>