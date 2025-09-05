import {create} from 'zustand';

export const useStore = create((set) => {
  // Инициализация: загружаем данные пользователя из localStorage
  const initializeUser = () => {
    try {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        return JSON.parse(savedUser);
      }
    } catch (error) {
      console.error('Ошибка при загрузке данных пользователя из localStorage:', error);
      localStorage.removeItem('user'); // Удаляем поврежденные данные
    }
    return null;
  };

  return {
    user: initializeUser(),
    setUser: (user) => set({user}),
    
    // Предустановленные пользователи
    users: [
      {
        id: 1,
        email: 'e@mail.ru',
        password: '123',
        name: 'HR Manager',
        role: 'hr'
      },
      {
        id: 2,
        email: 'a@mail.ru',
        password: '123',
        name: 'Applicant',
        role: 'applicant'
      }
    ],
    
    // Функция авторизации
    login: (email, password) => {
      const user = useStore.getState().users.find(u => u.email === email && u.password === password);
      if (user) {
        const userData = { ...user, password: undefined }; // Убираем пароль из состояния
        set({ user: userData });
        
        // Сохраняем данные пользователя в localStorage
        localStorage.setItem('user', JSON.stringify(userData));
        
        return { success: true, user: userData };
      }
      return { success: false, error: 'Неверный email или пароль' };
    },
    
    // Функция регистрации
    register: (email, password) => {
      const existingUser = useStore.getState().users.find(u => u.email === email);
      if (existingUser) {
        return { success: false, error: 'Пользователь с таким email уже существует' };
      }
      
      const newUser = {
        id: Date.now(),
        email,
        password,
        name: email.split('@')[0],
        role: 'applicant' // По умолчанию роль applicant
      };
      
      const userData = { ...newUser, password: undefined };
      
      set(state => ({
        users: [...state.users, newUser],
        user: userData
      }));
      
      // Сохраняем данные пользователя в localStorage
      localStorage.setItem('user', JSON.stringify(userData));
      
      return { success: true, user: userData };
    },
    vacancies: [
      {
        vacancyId: 1,
        name: 'Продуктовый дизайнер',
        status: 'active',
        department: 'Отдел внутренних коммуникаций',
        responses: 1376,
        responsesWithout: 1376,
        date: '2024-01-15',
      },
      {
        vacancyId: 2,
        name: 'Frontend разработчик',
        status: 'active',
        department: 'Отдел разработки',
        responses: 892,
        responsesWithout: 892,
        date: '2024-01-14',
      },
      {
        vacancyId: 3,
        name: 'UX/UI дизайнер',
        status: 'active',
        department: 'Отдел дизайна',
        responses: 654,
        responsesWithout: 654,
        date: '2024-01-13',
      },
      {
        vacancyId: 4,
        name: 'Product Manager',
        status: 'active',
        department: 'Отдел продуктов',
        responses: 445,
        responsesWithout: 445,
        date: '2024-01-12',
      },
      {
        vacancyId: 5,
        name: 'Backend разработчик',
        status: 'active',
        department: 'Отдел разработки',
        responses: 567,
        responsesWithout: 567,
        date: '2024-01-11',
      },
      {
        vacancyId: 6,
        name: 'QA инженер',
        status: 'active',
        department: 'Отдел тестирования',
        responses: 234,
        responsesWithout: 234,
        date: '2024-01-10',
      },
      {
        vacancyId: 7,
        name: 'DevOps инженер',
        status: 'active',
        department: 'Отдел инфраструктуры',
        responses: 123,
        responsesWithout: 123,
        date: '2024-01-09',
      },
      {
        vacancyId: 8,
        name: 'Аналитик данных',
        status: 'active',
        department: 'Отдел аналитики',
        responses: 345,
        responsesWithout: 345,
        date: '2024-01-08',
      },
    ],
    
    // Данные об откликах для каждой вакансии
    responses: {
      1: [
        { candidateId: 1, candidateName: 'Иван Петрович Петров', cvScore: 85, status: 'reviewed' },
        { candidateId: 2, candidateName: 'Мария Александровна Сидорова', cvScore: 92, status: 'pending' },
        { candidateId: 3, candidateName: 'Алексей Сергеевич Козлов', cvScore: 78, status: 'rejected' },
        { candidateId: 4, candidateName: 'Елена Владимировна Волкова', cvScore: 88, status: 'reviewed' },
        { candidateId: 5, candidateName: 'Дмитрий Игоревич Морозов', cvScore: 95, status: 'approved' },
      ],
      2: [
        { candidateId: 6, candidateName: 'Анна Михайловна Смирнова', cvScore: 87, status: 'reviewed' },
        { candidateId: 7, candidateName: 'Сергей Николаевич Новиков', cvScore: 91, status: 'pending' },
        { candidateId: 8, candidateName: 'Ольга Дмитриевна Лебедева', cvScore: 82, status: 'reviewed' },
      ],
      3: [
        { candidateId: 9, candidateName: 'Павел Андреевич Соколов', cvScore: 89, status: 'approved' },
        { candidateId: 10, candidateName: 'Татьяна Сергеевна Кузнецова', cvScore: 76, status: 'rejected' },
      ],
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
      // Удаляем данные пользователя из localStorage
      localStorage.removeItem('user');
      
      set({
        user: null,
        vacancies: []
      });
    },
  };
});
