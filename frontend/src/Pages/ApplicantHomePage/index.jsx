import React, {useState, useEffect} from 'react';
import {useStore} from '../../App/store';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Badge} from '../../components/ui/badge';
import {Button} from '../../components/ui/button';
import VacancyCard from './components/VacancyCard';
import ApplicationCard from './components/ApplicationCard';

const ApplicantHomePage = () => {
  const {
    user,
    applicantApplications,
    jobApplications,
    fetchApplicantApplications,
    fetchJobApplications,
    getFilteredVacancies,
    uploadResume,
  } = useStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingApplications, setIsLoadingApplications] = useState(false);
  const [isUploadingResume, setIsUploadingResume] = useState(false);
  const [resumeNotification, setResumeNotification] = useState(null);

  // Получаем отфильтрованные вакансии (исключая те, на которые уже подан отклик)
  const filteredVacancies = getFilteredVacancies();

  // Загружаем вакансии и отклики для апликанта при монтировании компонента
  useEffect(() => {
    if (user?.id) {
      const loadData = async () => {
        // Загружаем вакансии
        setIsLoading(true);
        try {
          await fetchApplicantApplications();
        } catch (error) {
          console.error('Ошибка при загрузке вакансий:', error);
        } finally {
          setIsLoading(false);
        }

        // Загружаем отклики
        setIsLoadingApplications(true);
        try {
          await fetchJobApplications();
        } catch (error) {
          console.error('Ошибка при загрузке откликов:', error);
        } finally {
          setIsLoadingApplications(false);
        }
      };
      loadData();
    }
  }, [user?.id, fetchApplicantApplications, fetchJobApplications]);

  const handleResumeUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Валидация файла
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    const maxSize = 5 * 1024 * 1024; // 5MB

    if (!allowedTypes.includes(file.type)) {
      setResumeNotification({
        type: 'error',
        message: 'Пожалуйста, выберите файл PDF или Word (.doc, .docx)',
      });
      setTimeout(() => setResumeNotification(null), 5000);
      return;
    }

    if (file.size > maxSize) {
      setResumeNotification({
        type: 'error',
        message: 'Размер файла не должен превышать 5MB',
      });
      setTimeout(() => setResumeNotification(null), 5000);
      return;
    }

    setIsUploadingResume(true);
    setResumeNotification(null);

    try {
      const result = await uploadResume(file);
      if (result.success) {
        setResumeNotification({
          type: 'success',
          message: 'Резюме успешно обновлено!',
        });
        setTimeout(() => setResumeNotification(null), 5000);
      } else {
        setResumeNotification({
          type: 'error',
          message: result.error || 'Ошибка при загрузке резюме',
        });
      }
    } catch {
      setResumeNotification({
        type: 'error',
        message: 'Ошибка при загрузке резюме. Попробуйте позже.',
      });
    } finally {
      setIsUploadingResume(false);
      // Очищаем input
      event.target.value = '';
    }
  };

  return (
    <div className='flex flex-col gap-[20px]'>
      {/* Уведомления */}
      {resumeNotification && (
        <div
          className={`p-4 rounded-lg ${
            resumeNotification.type === 'success'
              ? 'bg-green-100 border border-green-300 text-green-800'
              : 'bg-red-100 border border-red-300 text-red-800'
          }`}
        >
          <div className='flex justify-between items-center'>
            <p className='font-medium'>{resumeNotification.message}</p>
            <button onClick={() => setResumeNotification(null)} className='ml-4 text-lg font-bold hover:opacity-70'>
              ×
            </button>
          </div>
        </div>
      )}

      {/* Приветствие */}
      <div className='bg-white rounded-[20px] p-6 shadow-sm'>
        <h1 className='text-[32px] font-bold text-gray-800 mb-2'>Добро пожаловать, {user?.name || 'Кандидат'}!</h1>
        <p className='text-[18px] text-gray-600'>Здесь вы можете просматривать свои отклики и доступные вакансии</p>
      </div>

      {/* Мои отклики */}
      <Card>
        <CardHeader>
          <CardTitle className='text-[24px] font-semibold'>Мои отклики</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingApplications ? (
            <div className='flex justify-center items-center py-8'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28]'></div>
              <span className='ml-2'>Загрузка откликов...</span>
            </div>
          ) : jobApplications.length > 0 ? (
            <div className='space-y-4 flex gap-[10px] flex-wrap'>
              {jobApplications.map((application) => (
                <ApplicationCard key={application.vacancyId} application={application} />
              ))}
            </div>
          ) : (
            <div className='text-center py-8 text-gray-500'>У вас пока нет откликов на вакансии</div>
          )}
        </CardContent>
      </Card>

      {/* Доступные вакансии */}
      <Card>
        <CardHeader>
          <CardTitle className='text-[24px] font-semibold'>
            Доступные вакансии
            {applicantApplications.length > 0 && filteredVacancies.length !== applicantApplications.length && (
              <span className='text-sm font-normal text-gray-500 ml-2'>
                (показано {filteredVacancies.length} из {applicantApplications.length},{' '}
                {applicantApplications.length - filteredVacancies.length} уже в откликах)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className='flex justify-center items-center py-8'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28]'></div>
              <span className='ml-2'>Загрузка вакансий...</span>
            </div>
          ) : filteredVacancies.length > 0 ? (
            <div className='space-y-4 flex gap-[10px] flex-wrap'>
              {filteredVacancies.map((vacancy) => (
                <VacancyCard key={vacancy.vacancyId} vacancy={vacancy} />
              ))}
            </div>
          ) : (
            <div className='text-center py-8 text-gray-500'>Нет доступных вакансий</div>
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
            <div className='relative'>
              <input
                type='file'
                id='resume-upload'
                accept='.pdf,.doc,.docx'
                onChange={handleResumeUpload}
                className='absolute inset-0 w-full h-full opacity-0 cursor-pointer'
                disabled={isUploadingResume}
              />
              <Button className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white' disabled={isUploadingResume}>
                {isUploadingResume ? 'Загрузка...' : 'Обновить резюме'}
              </Button>
            </div>
            <Button variant='outline'>Настройки профиля</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicantHomePage;
