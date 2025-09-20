import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Badge} from '../../components/ui/badge';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Progress} from '../../components/ui/progress';
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

      {/* Обратная связь от HR */}
      {application.cvFeedback && application.cvFeedback.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Обратная связь от HR</CardTitle>
            <p className='text-gray-600 text-sm'>
              Результаты анализа вашего резюме по ключевым критериям вакансии
            </p>
          </CardHeader>
          <CardContent className='space-y-6'>
            {application.cvFeedback.map((feedback, index) => (
              <div key={index} className='border rounded-lg p-4 bg-gray-50'>
                <div className='flex justify-between items-center mb-3'>
                  <h4 className='font-semibold text-lg text-gray-800'>{feedback.name}</h4>
                  <div className='flex items-center gap-2'>
                    <span className='text-sm text-gray-600'>Оценка:</span>
                    <Badge 
                      className={`px-3 py-1 text-sm font-medium ${
                        feedback.score >= 80 ? 'bg-green-100 text-green-800' :
                        feedback.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                        feedback.score >= 40 ? 'bg-orange-100 text-orange-800' :
                        'bg-red-100 text-red-800'
                      }`}
                    >
                      {feedback.score}/100
                    </Badge>
                  </div>
                </div>
                
                <div className='mb-4'>
                  <Progress 
                    value={feedback.score} 
                    className='w-full h-2'
                  />
                </div>

                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  {/* Сильные стороны */}
                  {feedback.strengths && feedback.strengths.length > 0 && (
                    <div>
                      <h5 className='font-medium text-green-700 mb-2 flex items-center gap-1'>
                        <svg className='w-4 h-4' fill='currentColor' viewBox='0 0 20 20'>
                          <path fillRule='evenodd' d='M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' clipRule='evenodd' />
                        </svg>
                        Сильные стороны
                      </h5>
                      <ul className='space-y-1'>
                        {feedback.strengths.map((strength, idx) => (
                          <li key={idx} className='text-sm text-gray-700 flex items-start gap-2'>
                            <span className='text-green-500 mt-1'>•</span>
                            <span>{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Слабые стороны */}
                  {feedback.weaknesses && feedback.weaknesses.length > 0 && (
                    <div>
                      <h5 className='font-medium text-orange-700 mb-2 flex items-center gap-1'>
                        <svg className='w-4 h-4' fill='currentColor' viewBox='0 0 20 20'>
                          <path fillRule='evenodd' d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z' clipRule='evenodd' />
                        </svg>
                        Области для развития
                      </h5>
                      <ul className='space-y-1'>
                        {feedback.weaknesses.map((weakness, idx) => (
                          <li key={idx} className='text-sm text-gray-700 flex items-start gap-2'>
                            <span className='text-orange-500 mt-1'>•</span>
                            <span>{weakness}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {/* Общая информация */}
            <div className='mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200'>
              <div className='flex items-start gap-3'>
                <svg className='w-5 h-5 text-blue-600 mt-0.5' fill='currentColor' viewBox='0 0 20 20'>
                  <path fillRule='evenodd' d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z' clipRule='evenodd' />
                </svg>
                <div>
                  <h5 className='font-medium text-blue-800 mb-1'>Информация об оценке</h5>
                  <p className='text-sm text-blue-700'>
                    Эта обратная связь сформирована на основе анализа вашего резюме системой искусственного интеллекта. 
                    Используйте эти рекомендации для подготовки к собеседованию и развития профессиональных навыков.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Результаты собеседования */}
      {application.interviewFeedback && (
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Результаты собеседования</CardTitle>
            <p className='text-gray-600 text-sm'>
              Обратная связь по результатам проведенного собеседования
            </p>
          </CardHeader>
          <CardContent className='space-y-6'>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
              {/* Сильные стороны */}
              {application.interviewFeedback.strengths && application.interviewFeedback.strengths.length > 0 && (
                <div className='bg-green-50 p-4 rounded-lg border border-green-200'>
                  <div className='flex items-center mb-3'>
                    <svg className='w-5 h-5 text-green-600 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                    </svg>
                    <h4 className='font-bold text-green-700'>Сильные стороны</h4>
                  </div>
                  <ul className='space-y-2'>
                    {application.interviewFeedback.strengths.map((strength, idx) => (
                      <li key={idx} className='text-sm text-green-800 flex items-start'>
                        <span className='text-green-600 mr-2'>•</span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Области для развития */}
              {application.interviewFeedback.weaknesses && application.interviewFeedback.weaknesses.length > 0 && (
                <div className='bg-orange-50 p-4 rounded-lg border border-orange-200'>
                  <div className='flex items-center mb-3'>
                    <svg className='w-5 h-5 text-orange-600 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' />
                    </svg>
                    <h4 className='font-bold text-orange-700'>Области для развития</h4>
                  </div>
                  <ul className='space-y-2'>
                    {application.interviewFeedback.weaknesses.map((weakness, idx) => (
                      <li key={idx} className='text-sm text-orange-800 flex items-start'>
                        <span className='text-orange-600 mr-2'>•</span>
                        {weakness}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            {/* Информация о результатах */}
            <div className='mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200'>
              <div className='flex items-start gap-3'>
                <svg className='w-5 h-5 text-blue-600 mt-0.5' fill='currentColor' viewBox='0 0 20 20'>
                  <path fillRule='evenodd' d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z' clipRule='evenodd' />
                </svg>
                <div>
                  <h5 className='font-medium text-blue-800 mb-1'>Информация о результатах собеседования</h5>
                  <p className='text-sm text-blue-700'>
                    Эта обратная связь сформирована на основе проведенного собеседования с использованием системы искусственного интеллекта. 
                    Используйте эти рекомендации для дальнейшего профессионального развития.
                  </p>
                </div>
              </div>
            </div>
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
