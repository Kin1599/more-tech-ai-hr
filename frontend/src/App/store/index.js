import {create} from 'zustand';

export const useStore = create((set) => {
  return {
    user: {
      name: 'John Doe',
    },
    setUser: (user) => set({user}),
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
    
    // Функции для работы с вакансиями
    addVacancy: (vacancy) => set((state) => ({
      vacancies: [...state.vacancies, { ...vacancy, vacancyId: Date.now() }]
    })),
    
    updateVacancy: (vacancyId, updates) => set((state) => ({
      vacancies: state.vacancies.map(v => 
        v.vacancyId === vacancyId ? { ...v, ...updates } : v
      )
    })),
    
    deleteVacancy: (vacancyId) => set((state) => ({
      vacancies: state.vacancies.filter(v => v.vacancyId !== vacancyId)
    })),
    
    // Функция выхода пользователя
    logout: () => set({
      user: null,
      vacancies: []
    }),
  };
});
