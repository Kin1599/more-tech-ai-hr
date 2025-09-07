import {create} from 'zustand';
import {getVacancies, login, register} from '../../Api';
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
    
    // Данные об откликах для каждой вакансии
    responses: {},
    
    // Функция для загрузки вакансий с API
    fetchVacancies: async () => {
      try {
        const vacancies = await getVacancies();
        set({ vacancies });
      } catch (error) {
        console.error('Ошибка при загрузке вакансий:', error);
      }
    },
    
    // Функции для работы с вакансиями
    addVacancy: (newVacancy) => set((state) => {
      const maxId = Math.max(...state.vacancies.map(v => v.vacancyId), 0);
      return {
        vacancies: [...state.vacancies, {
          ...newVacancy,
          vacancyId: maxId + 1
        }]
      };
    }),
    
    updateVacancy: (vacancyId, updates) => set((state) => ({
      vacancies: state.vacancies.map(v => 
        v.vacancyId === vacancyId ? { ...v, ...updates } : v
      )
    })),
    
    deleteVacancy: (vacancyId) => set((state) => ({
      vacancies: state.vacancies.filter(v => v.vacancyId !== vacancyId)
    })),
    
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
