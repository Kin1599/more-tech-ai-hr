import {create} from 'zustand';
import {getVacancies, getVacancy, getHRVacancy, getHRApplicant, updateVacancyStatus, getApplicantApplications, getApplicantVacancy, applyToVacancy, getApplicantJobApplications, getApplicantJobApplication, uploadResume, login, register, uploadCVFile} from '../../Api';
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
    
    // Состояние для уведомлений
    toasts: [],
    
    // Функции для управления уведомлениями
    addToast: (toast) => {
      const id = Date.now() + Math.random();
      const newToast = { id, ...toast };
      set((state) => ({ toasts: [...state.toasts, newToast] }));
      
      // Автоматически удаляем уведомление через 5 секунд
      if (toast.duration !== 0) {
        setTimeout(() => {
          set((state) => ({ toasts: state.toasts.filter(t => t.id !== id) }));
        }, toast.duration || 5000);
      }
      
      return id;
    },
    
    removeToast: (id) => {
      set((state) => ({ toasts: state.toasts.filter(t => t.id !== id) }));
    },
    
    successToast: (title, description) => {
      const id = Date.now() + Math.random();
      const newToast = { 
        id, 
        title, 
        description, 
        variant: 'success',
        duration: 5000
      };
      
      set((state) => ({ toasts: [...state.toasts, newToast] }));
      
      // Автоматически удаляем уведомление через 5 секунд
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter(t => t.id !== id) }));
      }, 5000);
      
      return id;
    },
    
    errorToast: (title, description) => {
      const id = Date.now() + Math.random();
      const newToast = { 
        id, 
        title, 
        description, 
        variant: 'destructive',
        duration: 5000
      };
      
      set((state) => ({ toasts: [...state.toasts, newToast] }));
      
      // Автоматически удаляем уведомление через 5 секунд
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter(t => t.id !== id) }));
      }, 5000);
      
      return id;
    },
    
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
    register: async (email, password, resumeFile, role = 'applicant') => {
      try {
        const response = await register(email, password, resumeFile, role);
        const { access_token, user_id, role: userRole } = response;
        
        const userData = {
          id: user_id,
          email,
          role: userRole,
          name: email.split('@')[0] // Генерируем имя из email
        };
        
        // Сохраняем токен и пользователя
        setStoredToken(access_token);
        setAuthToken(access_token);
        set({ user: userData });
        localStorage.setItem('user', JSON.stringify(userData));
        
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
    
    // Отклики на вакансии (job applications)
    jobApplications: [],
    
    // Функция для загрузки вакансий с API
    fetchVacancies: async () => {
      try {
        const vacancies = await getVacancies();
        set({ vacancies });
      } catch (error) {
        console.error('Ошибка при загрузке вакансий:', error);
        
        // Показываем уведомление только при ошибке
        set((state) => {
          const id = Date.now() + Math.random();
          const newToast = { 
            id, 
            title: 'Ошибка загрузки', 
            description: 'Не удалось загрузить вакансии', 
            variant: 'destructive',
            duration: 5000
          };
          return { toasts: [...state.toasts, newToast] };
        });
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
    
    // Функция для загрузки HR вакансии с деталями
    fetchHRVacancy: async (vacancyId) => {
      try {
        const vacancy = await getHRVacancy(vacancyId);
        return { success: true, data: vacancy };
      } catch (error) {
        console.error('Ошибка при загрузке HR вакансии:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке HR вакансии' 
        };
      }
    },
    
    // Функция для загрузки HR кандидата
    fetchHRApplicant: async (applicantId, vacancyId) => {
      try {
        const applicant = await getHRApplicant(applicantId, vacancyId);
        return { success: true, data: applicant };
      } catch (error) {
        console.error('Ошибка при загрузке HR кандидата:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке HR кандидата' 
        };
      }
    },
    
    // Функция для загрузки откликов апликанта
    fetchApplicantApplications: async () => {
      try {
        const applications = await getApplicantApplications();
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
    
    // Функция для загрузки конкретной вакансии апликанта
    fetchApplicantVacancy: async (vacancyId) => {
      try {
        const vacancy = await getApplicantVacancy(vacancyId);
        return { success: true, data: vacancy };
      } catch (error) {
        console.error('Ошибка при загрузке вакансии апликанта:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке вакансии' 
        };
      }
    },
    
    // Функция для подачи отклика на вакансию
    applyToVacancy: async (vacancyId) => {
      try {
        const result = await applyToVacancy(vacancyId);
        
        // После успешной подачи отклика обновляем список откликов
        if (result.success) {
          // Перезагружаем список откликов, чтобы получить актуальные данные
          const applicationsResult = await getApplicantJobApplications();
          if (applicationsResult.success) {
            set({ jobApplications: applicationsResult.data });
          }
        }
        
        return { success: true, data: result };
      } catch (error) {
        console.error('Ошибка при подаче отклика:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при подаче отклика' 
        };
      }
    },
    
    // Функция для загрузки откликов апликанта
    fetchJobApplications: async () => {
      try {
        const applications = await getApplicantJobApplications();
        set({ jobApplications: applications });
        return { success: true, data: applications };
      } catch (error) {
        console.error('Ошибка при загрузке откликов:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке откликов' 
        };
      }
    },
    
    // Функция для получения отфильтрованных вакансий (исключая те, на которые уже подан отклик и закрытые вакансии)
    getFilteredVacancies: () => {
      const state = useStore.getState();
      const appliedVacancyIds = state.jobApplications.map(app => app.vacancyId);
      return state.applicantApplications.filter(vacancy => 
        !appliedVacancyIds.includes(vacancy.vacancyId) && 
        vacancy.status !== 'closed' &&
        vacancy.status !== 'inactive'
      );
    },
    
    // Функция для загрузки деталей отклика
    fetchJobApplication: async (vacancyId) => {
      try {
        const application = await getApplicantJobApplication(vacancyId);
        return { success: true, data: application };
      } catch (error) {
        console.error('Ошибка при загрузке деталей отклика:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке деталей отклика' 
        };
      }
    },
    
    // Функция для загрузки резюме
    uploadResume: async (file) => {
      try {
        const result = await uploadResume(file);
        return { success: true, data: result };
      } catch (error) {
        console.error('Ошибка при загрузке резюме:', error);
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Ошибка при загрузке резюме' 
        };
      }
    },
    
    // Функция для загрузки CV
    uploadCV: async (file, vacancyId = null) => {
      try {
        const vacancyData = await uploadCVFile(file, vacancyId);
        
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
        
        // Показываем уведомление об успешной загрузке
        set((state) => {
          const id = Date.now() + Math.random();
          const newToast = { 
            id, 
            title: 'CV загружен', 
            description: vacancyId ? 'Вакансия обновлена' : 'Новая вакансия создана', 
            variant: 'success',
            duration: 3000
          };
          return { toasts: [...state.toasts, newToast] };
        });
        
        return { success: true, data: vacancyData };
      } catch (error) {
        console.error('Ошибка при загрузке CV:', error);
        
        // Показываем уведомление об ошибке
        set((state) => {
          const id = Date.now() + Math.random();
          const newToast = { 
            id, 
            title: 'Ошибка загрузки CV', 
            description: error.response?.data?.detail || 'Не удалось загрузить CV', 
            variant: 'destructive',
            duration: 5000
          };
          return { toasts: [...state.toasts, newToast] };
        });
        
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
