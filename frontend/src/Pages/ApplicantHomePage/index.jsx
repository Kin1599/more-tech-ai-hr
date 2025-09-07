import React, {useState, useEffect} from 'react';
import {useStore} from '../../App/Store';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Badge} from '../../components/ui/badge';
import {Button} from '../../components/ui/button';
import VacancyCard from './components/VacancyCard';

const ApplicantHomePage = () => {
  const {user, applicantApplications, fetchApplicantApplications} = useStore();
  const [isLoading, setIsLoading] = useState(false);

  // Загружаем отклики апликанта при монтировании компонента
  useEffect(() => {
    if (user?.id) {
      const loadApplications = async () => {
        setIsLoading(true);
        try {
          await fetchApplicantApplications(user.id);
        } catch (error) {
          console.error('Ошибка при загрузке откликов:', error);
        } finally {
          setIsLoading(false);
        }
      };
      loadApplications();
    }
  }, [user?.id, fetchApplicantApplications]);

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
          {isLoading ? (
            <div className='flex justify-center items-center py-8'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28]'></div>
              <span className='ml-2'>Загрузка откликов...</span>
            </div>
          ) : applicantApplications.length > 0 ? (
            <div className='space-y-4 flex gap-[10px] flex-wrap'>
              {applicantApplications.map((application) => (
                <VacancyCard key={application.vacancyID} vacancy={application} />
              ))}
            </div>
          ) : (
            <div className='text-center py-8 text-gray-500'>У вас пока нет откликов на вакансии</div>
          )}
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
