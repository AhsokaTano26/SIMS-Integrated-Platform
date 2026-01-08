<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
</script>

<style>
/* 基础样式重置，确保页面铺满屏幕 */
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>