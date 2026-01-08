import axios from 'axios';
import { ElMessage } from 'element-plus';

const service = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 5000
});

// 请求拦截
service.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// 响应拦截
service.interceptors.response.use(
  response => response.data,
  error => {
    let msg = '网络错误，请稍后再试';
    const response = error.response;

    if (response) {
      const data = response.data;
      const status = response.status;

      // 1. 处理 400 字段验证错误 (注册、表单提交)
      if (status === 400) {
        if (typeof data === 'object') {
          const firstKey = Object.keys(data)[0];
          const firstError = data[firstKey];
          const fieldMap = {
            username: '用户名',
            password: '密码',
            student_id: '学号/工号',
            phone: '手机号',
            college: '学院'
          };
          const fieldName = fieldMap[firstKey] || firstKey;
          msg = Array.isArray(firstError) ? `${fieldName}: ${firstError[0]}` : firstError;
        } else {
          msg = '请求参数错误';
        }
      }

      // 2. 处理 401 授权错误 (登录失败或 Token 过期)
      else if (status === 401) {
        // 如果是在登录页面收到的 401，说明是账号密码错
        if (window.location.pathname.includes('/login')) {
          msg = '账号或密码错误，请核对后重试';
        } else {
          // 如果是在其他页面收到的 401，说明 Token 过期
          msg = '登录已过期，请重新登录';
          localStorage.clear();
          // 延迟一秒跳转，确保用户看清错误提示
          setTimeout(() => {
            window.location.href = '/login';
          }, 1000);
        }
      }

      // 3. 处理 403 权限错误
      else if (status === 403) {
        msg = '权限不足，无法访问';
      }

      // 4. 处理 500 以上服务器错误
      else if (status >= 500) {
        msg = '服务器开小差了，请联系管理员';
      }

      // 5. 其他情况
      else {
        msg = data.detail || '操作失败';
      }
    } else if (error.message.includes('timeout')) {
      msg = '请求超时，请检查网络';
    }

    // 执行弹窗提示
    ElMessage({
      message: msg,
      type: 'error',
      duration: 5000,
      showClose: true // 增加关闭按钮
    });

    return Promise.reject(error);
  }
);

export default service;