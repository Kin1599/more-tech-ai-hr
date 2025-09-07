import React from 'react';
import {useStore} from '../../App/Store';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Badge} from '../../components/ui/badge';
import {Button} from '../../components/ui/button';
import VacancyCard from './components/VacancyCard';

const ApplicantHomePage = () => {
  const {user} = useStore();

  // Данные о последних откликах кандидата
  const recentApplications = [
    {
      vacancyId: 2,
      name: 'Frontend разработчик',
      department: 'Отдел разработки',
      status: 'pending',
      region: 'Санкт-Петербург',
      busyType: 'allTime',
      hr: {
        name: 'Михаил Соколов',
        contact: 'mikhail.sokolov@vtb.ru',
      },
      applicationDate: '2024-01-20',
    },
    {
      vacancyId: 3,
      name: 'UX/UI дизайнер',
      department: 'Отдел дизайна',
      status: 'approved',
      region: 'Москва',
      busyType: 'projectTime',
      hr: {
        name: 'Елена Волкова',
        contact: 'elena.volkova@vtb.ru',
      },
      applicationDate: '2024-01-18',
    },
    {
      vacancyId: 4,
      name: 'Product Manager',
      department: 'Отдел продуктов',
      status: 'reviewed',
      region: 'Москва',
      busyType: 'allTime',
      hr: {
        name: 'Дмитрий Морозов',
        contact: 'dmitry.morozov@vtb.ru',
      },
      applicationDate: '2024-01-15',
    },
  ];

  return (
    <div className='flex flex-col gap-[20px]'>
      {/* Приветствие */}
      <div className='bg-white rounded-[20px] p-6 shadow-sm'>
        <h1 className='text-[32px] font-bold text-gray-800 mb-2'>Добро пожаловать, {user?.name || 'Кандидат'}!</h1>
        <p className='text-[18px] text-gray-600'>Здесь вы можете отслеживать свои отклики и статус заявок</p>
      </div>

      {/* Последние отклики */}
      <Card>
        <CardHeader>
          <CardTitle className='text-[24px] font-semibold'>Последние отклики</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4 flex gap-[10px] flex-wrap'>
            {recentApplications.map((application) => (
              <VacancyCard key={application.vacancyId} vacancy={application} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Быстрые действия */}
      <Card>
        <CardHeader>
          <CardTitle className='text-[24px] font-semibold'>Быстрые действия</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='flex gap-4'>
            <Button className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white'>Обновить резюме</Button>
            <Button variant='outline'>Настройки профиля</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicantHomePage;
