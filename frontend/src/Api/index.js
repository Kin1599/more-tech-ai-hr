import {apiClient} from './config';
import {http} from './http';

export {API_BASE_URL, apiClient} from './config';
export {http} from './http';

// API функция для получения вакансий
export const getVacancies = async () => {
  const response = await apiClient.get('/api/hr/vacancies');
  return response.data;
};

// API функция для получения HR вакансии с деталями
export const getHRVacancy = async (vacancyId) => {
  const response = await apiClient.get(`/api/hr/vacancies/${vacancyId}`);
  return response.data;
};

// API функция для получения HR кандидата
export const getHRApplicant = async (applicantId, vacancyId) => {
  const response = await apiClient.get(`/api/hr/applicants/${applicantId}?vacancy_id=${vacancyId}&applicant_id=${applicantId}`);
  return response.data;
};

// API функция для получения конкретной вакансии
export const getVacancy = async (vacancyId) => {
  const response = await apiClient.get(`/api/hr/vacancies/${vacancyId}`);
  return response.data;
};

// API функция для изменения статуса вакансии
export const updateVacancyStatus = async (vacancyId, status) => {
  const response = await apiClient.put(`/api/hr/vacancies/${vacancyId}/status`, {
    status
  });
  return response.data;
};

// API функция для получения откликов апликанта
export const getApplicantApplications = async () => {
  const response = await apiClient.get(`/api/applicant/vacancies`);
  return response.data;
};

// API функция для получения конкретной вакансии апликанта
export const getApplicantVacancy = async (vacancyId) => {
  const response = await apiClient.get(`/api/applicant/vacancies/${vacancyId}`);
  return response.data[0];
};

// API функция для подачи отклика на вакансию
export const applyToVacancy = async (vacancyId) => {
  const response = await apiClient.post(`/api/applicant/job_applications/${vacancyId}`);
  return response.data;
};

// API функция для получения откликов апликанта
export const getApplicantJobApplications = async () => {
  const response = await apiClient.get('/api/applicant/job_applications');
  return response.data;
};

// API функция для получения деталей отклика
export const getApplicantJobApplication = async (vacancyId) => {
  const response = await apiClient.get(`/api/applicant/job_applications/${vacancyId}`);
  return response.data;
};

// API функция для загрузки резюме
export const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/api/user/me/resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
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

export const register = async (email, password, resumeFile, role = 'applicant') => {
  const formData = new FormData();
  formData.append('email', email);
  formData.append('password', password);
  formData.append('role', role);
  if (resumeFile) {
    formData.append('cv', resumeFile);
  }

  const response = await apiClient.post('/api/auth/register', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// API функция для загрузки CV
export const uploadCVFile = async (file, vacancyId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const url = vacancyId 
    ? `/api/hr/vacancies/${vacancyId}` 
    : '/api/hr/vacancies';
  
  const method = vacancyId ? 'PUT' : 'POST';
  
  const response = await apiClient({
    method,
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// API функция для получения ссылки на интервью
export const getInterviewLink = async (vacancyId) => {
  const response = await apiClient.get(`/api/applicant/job_applications/${vacancyId}/interview?vacancy_id=${vacancyId}`);
  return response.data;
};

export const api = {
  http,
  getVacancies,
  getVacancy,
  updateVacancyStatus,
  getApplicantApplications,
  login,
  register,
  uploadCV: uploadCVFile,
  getInterviewLink,
};
