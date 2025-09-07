import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Функции для работы с токеном
export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

export const getStoredToken = () => {
  return localStorage.getItem('access_token');
};

export const setStoredToken = (token) => {
  localStorage.setItem('access_token', token);
};

export const removeStoredToken = () => {
  localStorage.removeItem('access_token');
};

// Инициализация токена при загрузке
const token = getStoredToken();
if (token) {
  setAuthToken(token);
}

apiClient.interceptors.response.use((response) => {
  return response;
}, (error) => {
  // Если токен истек (401), удаляем его
  if (error.response?.status === 401) {
    removeStoredToken();
    setAuthToken(null);
    // Перенаправляем на страницу логина
    window.location.href = '/login';
  }
  return Promise.reject(error);
});
