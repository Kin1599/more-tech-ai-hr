import {create} from 'zustand';
import {getVacancies, getVacancy, updateVacancyStatus, getApplicantApplications, login, register, uploadCV} from '../../Api';
import {setAuthToken, setStoredToken, removeStoredToken, getStoredToken} from '../../Api/config';

export const useStore = create((set) => {
  // Инициализация: загружаем данные пользователя из localStorage
  const initializeUser = () => {
    try {
      const savedUser = localStorage.getItem('user');
      const token = getStoredToken();
      if (savedUser && token) {
        return JSON.parse(savedUser);
      }
    } catch (error) {
      console.error('Ошибка при загрузке данных пользователя из localStorage:', error);
      localStorage.removeItem('user');
      removeStoredToken();
    }
    return null;
  };

  return {
    user: initializeUser(),
    setUser: (user) => set({user}),
    
    // Предустановленные пользователи
    // Мок данные пользователей больше не нужны - используем API
    
    // Функция авторизации
    login: async (email, password) => {
      try {
        const response = await login(email, password);
        const { access_token, user_id, role } = response;
        
        const userData = {
          id: user_id,
          email,
          role,
          name: email.split('@')[0] // Генерируем имя из email
        };
        
        // Сохраняем токен и пользователя
        setStoredToken(access_token);
        setAuthToken(access_token);
        set({ user: userData });
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Очищаем сохраненный URL для редиректа (если есть)
        const savedUrl = localStorage.getItem('redirectAfterLogin');
        if (savedUrl) {
          localStorage.removeItem('redirectAfterLogin');
        }
        
        return { success: true, user: userData };
      } catch (error) {
        console.error('Ошибка при входе:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при входе в систему' 
        };
      }
    },
    
    // Функция регистрации
    register: async (email, password, resumeFile) => {
      try {
        const response = await register(email, password, resumeFile);
        const { access_token, user_id, role } = response;
        
        const userData = {
          id: user_id,
          email,
          role,
          name: email.split('@')[0] // Генерируем имя из email
        };
        
        // Сохраняем токен и пользователя
        setStoredToken(access_token);
        setAuthToken(access_token);
        set({ user: userData });
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Очищаем сохраненный URL для редиректа (если есть)
        const savedUrl = localStorage.getItem('redirectAfterLogin');
        if (savedUrl) {
          localStorage.removeItem('redirectAfterLogin');
        }
        
        return { success: true, user: userData };
      } catch (error) {
        console.error('Ошибка при регистрации:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при регистрации' 
        };
      }
    },
    vacancies: [],
    
    // Отклики апликанта
    applicantApplications: [],
    
    // Функция для загрузки вакансий с API
    fetchVacancies: async () => {
      try {
        const vacancies = await getVacancies();
        set({ vacancies });
      } catch (error) {
        console.error('Ошибка при загрузке вакансий:', error);
      }
    },
    
    // Функция для загрузки конкретной вакансии
    fetchVacancy: async (vacancyId) => {
      try {
        const vacancy = await getVacancy(vacancyId);
        return { success: true, data: vacancy };
      } catch (error) {
        console.error('Ошибка при загрузке вакансии:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке вакансии' 
        };
      }
    },
    
    // Функция для загрузки откликов апликанта
    fetchApplicantApplications: async (applicantId) => {
      try {
        const applications = await getApplicantApplications(applicantId);
        set({ applicantApplications: applications });
        return { success: true, data: applications };
      } catch (error) {
        console.error('Ошибка при загрузке откликов апликанта:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке откликов' 
        };
      }
    },
    
    // Функция для загрузки CV
    uploadCV: async (file, vacancyId = null) => {
      try {
        const vacancyData = await uploadCV(file, vacancyId);
        
        if (vacancyId) {
          // Обновляем существующую вакансию
          set((state) => ({
            vacancies: state.vacancies.map(v => 
              v.vacancyId === vacancyId ? { ...v, ...vacancyData } : v
            )
          }));
        } else {
          // Добавляем новую вакансию
          set((state) => ({
            vacancies: [...state.vacancies, vacancyData]
          }));
        }
        
        return { success: true, data: vacancyData };
      } catch (error) {
        console.error('Ошибка при загрузке CV:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке CV' 
        };
      }
    },
    
    // Функция для обновления вакансии
    updateVacancy: (vacancyId, updates) => set((state) => {
      const existingIndex = state.vacancies.findIndex(v => v.vacancyId === vacancyId);
      
      if (existingIndex !== -1) {
        // Обновляем существующую вакансию
        return {
          vacancies: state.vacancies.map(v => 
            v.vacancyId === vacancyId ? { ...v, ...updates } : v
          )
        };
      } else {
        // Добавляем новую вакансию
        return {
          vacancies: [...state.vacancies, { ...updates, vacancyId }]
        };
      }
    }),
    
    // Функция для изменения статуса вакансии
    changeVacancyStatus: async (vacancyId, status) => {
      try {
        await updateVacancyStatus(vacancyId, status);
        
        // Обновляем статус в локальном состоянии
        set((state) => ({
          vacancies: state.vacancies.map(v => 
            v.vacancyId === vacancyId ? { ...v, status } : v
          )
        }));
        
        return { success: true };
      } catch (error) {
        console.error('Ошибка при изменении статуса вакансии:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при изменении статуса вакансии' 
        };
      }
    },
    
    // Функция выхода пользователя
    logout: () => {
      // Удаляем данные пользователя и токен из localStorage
      localStorage.removeItem('user');
      removeStoredToken();
      setAuthToken(null);
      
      set({
        user: null
      });
    },
  };
});
