import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Badge} from '../../components/ui/badge';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {useStore} from '../../App/store';
import {capitalizeFirst} from '../../lib/utils';
import {getInterviewData} from '../../Api';

const ApplicationDetailPage = () => {
  const {vacancyId} = useParams();
  const navigate = useNavigate();
  const {fetchJobApplication} = useStore();

  const [application, setApplication] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [linkCopied, setLinkCopied] = useState(false);
  const [showInterviewDialog, setShowInterviewDialog] = useState(false);
  const [isGettingInterviewLink, setIsGettingInterviewLink] = useState(false);

  useEffect(() => {
    const loadApplication = async () => {
      if (vacancyId) {
        setIsLoading(true);
        try {
          const result = await fetchJobApplication(parseInt(vacancyId));
          if (result.success) {
            setApplication(result.data);
          } else {
            console.error('Ошибка при загрузке отклика:', result.error);
          }
        } catch (error) {
          console.error('Ошибка при загрузке отклика:', error);
        } finally {
          setIsLoading(false);
        }
      }
    };
    loadApplication();
  }, [vacancyId, fetchJobApplication]);

  const getStatusText = (status) => {
    switch (status) {
      case 'rejected':
        return 'Отклонен';
      case 'cvReview':
        return 'Просмотр резюме';
      case 'interview':
        return 'Собеседование';
      case 'waitResult':
        return 'Ожидание результата';
      case 'approved':
        return 'Одобрен';
      default:
        return 'Неизвестно';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'cvReview':
        return 'bg-yellow-100 text-yellow-800';
      case 'interview':
        return 'bg-blue-100 text-blue-800';
      case 'waitResult':
        return 'bg-purple-100 text-purple-800';
      case 'approved':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getBusyTypeText = (busyType) => {
    switch (busyType) {
      case 'allTime':
        return 'Полная занятость';
      case 'partTime':
        return 'Частичная занятость';
      case 'projectTime':
        return 'Проектная занятость';
      default:
        return 'Не указано';
    }
  };

  const handleGetInterviewLink = () => {
    setShowInterviewDialog(true);
  };

  const confirmInterview = async () => {
    setIsGettingInterviewLink(true);
    try {
      const data = await getInterviewData(vacancyId);
      setApplication((prev) => ({...prev, roomId: data.roomId, token: data.token}));
      setShowInterviewDialog(false);
      // Переходим на страницу видеособеседования
      navigate(`/interview/${data.roomId}/${data.token}`);
    } catch (error) {
      console.error('Ошибка при получении данных для интервью:', error);
    } finally {
      setIsGettingInterviewLink(false);
    }
  };

  if (isLoading) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28] mb-4'></div>
        <h1 className='text-2xl font-semibold mb-4'>Загрузка отклика...</h1>
      </div>
    );
  }

  if (!application) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <h1 className='text-2xl font-semibold mb-4'>Отклик не найден</h1>
        <Button onClick={() => navigate('/applicant')}>Вернуться к списку</Button>
      </div>
    );
  }

  return (
    <div className='flex flex-col gap-[20px]'>
      {/* Уведомления */}
      {linkCopied && (
        <div className='p-4 rounded-lg bg-green-100 border border-green-300 text-green-800'>
          <div className='flex justify-between items-center'>
            <p className='font-medium'>Ссылка на интервью скопирована!</p>
            <button onClick={() => setLinkCopied(false)} className='ml-4 text-lg font-bold hover:opacity-70'>
              ×
            </button>
          </div>
        </div>
      )}

      {/* Кнопка назад */}
      <div>
        <Button
          onClick={() => navigate('/applicant')}
          variant='outline'
          className='flex items-center gap-2 cursor-pointer'
        >
          <svg className='w-4 h-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M15 19l-7-7 7-7' />
          </svg>
          Назад к списку откликов
        </Button>
      </div>

      {/* Заголовок отклика */}
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-[32px] font-bold text-gray-800 mb-2'>{capitalizeFirst(application.name)}</h1>
          <p className='text-[18px] text-gray-600'>{capitalizeFirst(application.region)}</p>
        </div>
        <Badge className={`px-4 py-2 text-lg font-medium ${getStatusColor(application.status)}`}>
          {getStatusText(application.status)}
        </Badge>
      </div>

      {/* Основная информация */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Информация о вакансии</CardTitle>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Название:</span>
              <span className='font-medium'>{capitalizeFirst(application.name)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Регион:</span>
              <span className='font-medium'>{capitalizeFirst(application.region)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Тип занятости:</span>
              <span className='font-medium'>{getBusyTypeText(application.busyType)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Статус отклика:</span>
              <span className='font-medium'>{getStatusText(application.status)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Контактная информация</CardTitle>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='flex justify-between'>
              <span className='text-gray-600'>HR-менеджер:</span>
              <span className='font-medium'>{capitalizeFirst(application.hr?.name) || 'Не указан'}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Email:</span>
              <span className='font-medium text-blue-600'>{application.hr?.contact || 'Не указан'}</span>
            </div>
            {application.interviewLink && (
              <div className='flex justify-between'>
                <span className='text-gray-600'>Ссылка на интервью:</span>
                <a
                  href={application.interviewLink}
                  target='_blank'
                  rel='noopener noreferrer'
                  className='font-medium text-blue-600 hover:underline'
                >
                  Перейти к интервью
                </a>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Рекомендации по интервью */}
      {application.interviewRecomendation && (
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Рекомендации по интервью</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-gray-700 leading-relaxed'>{application.interviewRecomendation}</p>
          </CardContent>
        </Card>
      )}

      {/* Кнопки действий */}
      <div className='flex gap-4 justify-center flex-wrap'>
        {application.status === 'rejected' ? (
          <Button className='bg-gray-500 hover:bg-gray-600 text-white px-8 py-3 text-lg' disabled>
            Отклик отклонен
          </Button>
        ) : application.status === 'approved' ? (
          <Button className='bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg'>Отклик одобрен</Button>
        ) : application.status === 'interview' ? (
          <>
            <Button
              className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white px-8 py-3 text-lg cursor-pointer'
              onClick={handleGetInterviewLink}
            >
              Пройти собеседование
            </Button>
          </>
        ) : application.interviewLink ? (
          <Button
            className='bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg'
            onClick={() => window.open(application.interviewLink, '_blank')}
          >
            Пройти интервью
          </Button>
        ) : (
          <Button className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white px-8 py-3 text-lg' disabled>
            Ожидание ответа
          </Button>
        )}

        <Button variant='outline' className='px-8 py-3 text-lg cursor-pointer'>
          Связаться с HR
        </Button>
      </div>

      {/* Модальное окно подтверждения собеседования */}
      <Dialog open={showInterviewDialog} onOpenChange={setShowInterviewDialog}>
        <DialogContent className='sm:max-w-md'>
          <DialogHeader>
            <DialogTitle className='text-xl font-semibold'>Подтверждение собеседования</DialogTitle>
            <DialogDescription className='text-base leading-relaxed'>
              Вы точно готовы пройти собеседование? Оно займет у вас 30 минут. Вас не должны отвлекать, и вы должны быть
              в тихом месте с хорошим интернет-соединением.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className='flex gap-3'>
            <Button
              onClick={confirmInterview}
              disabled={isGettingInterviewLink}
              className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white cursor-pointer'
            >
              {isGettingInterviewLink ? 'Получение ссылки...' : 'Да, готов'}
            </Button>
            <Button
              variant='outline'
              onClick={() => setShowInterviewDialog(false)}
              disabled={isGettingInterviewLink}
              className='cursor-pointer'
            >
              Нет
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ApplicationDetailPage;
