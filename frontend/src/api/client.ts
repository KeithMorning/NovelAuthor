import axios from 'axios';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 统一错误处理
    if (error.response) {
      const { status, data } = error.response;

      if (status === 404) {
        console.error('资源不存在:', data);
      } else if (status === 500) {
        console.error('服务器错误:', data);
      }
    } else if (error.request) {
      console.error('网络错误:', error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
