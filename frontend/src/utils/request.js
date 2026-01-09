import axios from 'axios';
import { ElMessage } from 'element-plus';

const service = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', // 你的 Django API 地址
  timeout: 5000
});

// 请求拦截：自动注入 Token
service.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：处理错误
service.interceptors.response.use(
  response => response.data,
  error => {
    // 1. 获取错误信息和请求的 URL
    const msg = error.response?.data?.detail || error.response?.data?.error || '网络错误';
    const config = error.config; // 获取请求的配置信息

    // 2. 定义不需要自动跳转登录的“白名单”接口路径
    const whiteList = ['/auth/users/verify-user/', '/auth/users/self-reset-password/'];
    const isWhiteList = whiteList.some(path => config.url.includes(path));

    // 3. 只有不在白名单内，且状态码为 401 时才跳转
    if (error.response?.status === 401 && !isWhiteList) {
      ElMessage.error('登录失效，请重新登录');
      localStorage.clear();
      window.location.href = '/login';
    } else {
      // 如果是白名单接口报错，只弹窗提示错误，不跳转
      ElMessage.error(msg);
    }

    return Promise.reject(error);
  }
);

export default service;