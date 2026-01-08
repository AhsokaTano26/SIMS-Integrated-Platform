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
    const msg = error.response?.data?.detail || '网络错误';
    ElMessage.error(msg);
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default service;