import React from 'react';
import {useStore} from '../../App/Store';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Badge} from '../../components/ui/badge';
import {Button} from '../../components/ui/button';

const ApplicantHomePage = () => {
  const {user} = useStore();

  return (
    <div className='flex flex-col gap-[20px]'>
      {/* Приветствие */}
      <div className='bg-white rounded-[20px] p-6 shadow-sm'>
        <h1 className='text-[32px] font-bold text-gray-800 mb-2'>Добро пожаловать, {user?.name || 'Кандидат'}!</h1>
        <p className='text-[18px] text-gray-600'>Здесь вы можете отслеживать свои отклики и статус заявок</p>
      </div>

      {/* Статистика */}
      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <Card>
          <CardHeader className='pb-2'>
            <CardTitle className='text-[16px] font-medium text-gray-600'>Всего откликов</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-[32px] font-bold text-blue-600'>12</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='pb-2'>
            <CardTitle className='text-[16px] font-medium text-gray-600'>На рассмотрении</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-[32px] font-bold text-yellow-600'>5</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='pb-2'>
            <CardTitle className='text-[16px] font-medium text-gray-600'>Одобрено</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-[32px] font-bold text-green-600'>3</div>
          </CardContent>
        </Card>
      </div>

      {/* Последние отклики */}
      <Card>
        <CardHeader>
          <CardTitle className='text-[24px] font-semibold'>Последние отклики</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4'>
            <div className='flex justify-between items-center p-4 border rounded-lg'>
              <div>
                <h3 className='text-[18px] font-semibold'>Frontend разработчик</h3>
                <p className='text-gray-600'>Банк ВТБ</p>
              </div>
              <Badge className='bg-yellow-100 text-yellow-800'>На рассмотрении</Badge>
            </div>

            <div className='flex justify-between items-center p-4 border rounded-lg'>
              <div>
                <h3 className='text-[18px] font-semibold'>UX/UI дизайнер</h3>
                <p className='text-gray-600'>Банк ВТБ</p>
              </div>
              <Badge className='bg-green-100 text-green-800'>Одобрено</Badge>
            </div>

            <div className='flex justify-between items-center p-4 border rounded-lg'>
              <div>
                <h3 className='text-[18px] font-semibold'>Product Manager</h3>
                <p className='text-gray-600'>Банк ВТБ</p>
              </div>
              <Badge className='bg-blue-100 text-blue-800'>Собеседование</Badge>
            </div>
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
            <Button className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white'>Подать новый отклик</Button>
            <Button variant='outline'>Обновить резюме</Button>
            <Button variant='outline'>Настройки профиля</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicantHomePage;
