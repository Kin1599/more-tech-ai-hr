import {apiClient} from './config';
import {http} from './http';

export {API_BASE_URL, apiClient} from './config';
export {http} from './http';

// API функция для получения вакансий
export const getVacancies = async () => {
  const response = await apiClient.get('/api/vacancies');
  return response.data;
};

// API функции для аутентификации
export const login = async (email, password) => {
  const response = await apiClient.post('/api/auth/login', {
    email,
    password
  });
  return response.data;
};

export const register = async (email, password, resumeFile) => {
  const formData = new FormData();
  formData.append('email', email);
  formData.append('password', password);
  formData.append('role', 'applicant');
  formData.append('resume', resumeFile);

  const response = await apiClient.post('/api/auth/register', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const api = {
  http,
  getVacancies,
  login,
  register,
};
