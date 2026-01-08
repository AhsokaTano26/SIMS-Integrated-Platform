import { defineStore } from 'pinia';
import request from '../utils/request';

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    userInfo: JSON.parse(localStorage.getItem('user_info') || '{}')
  }),
  actions: {
    async login(loginForm) {
      const res = await request.post('/auth/login/', loginForm);
      this.token = res.access;
      this.userInfo = { username: res.username, role: res.role, id: res.id };

      localStorage.setItem('access_token', res.access);
      localStorage.setItem('user_info', JSON.stringify(this.userInfo));
      return res;
    },
    logout() {
      this.token = '';
      this.userInfo = {};
      localStorage.clear();
    }
  }
});