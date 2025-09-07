import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Badge} from '../../components/ui/badge';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {useStore} from '../../App/Store';

const ApplicantVacancyPage = () => {
  const {vacancyId} = useParams();
  const navigate = useNavigate();
  const {vacancies} = useStore();

  const [vacancy, setVacancy] = useState(null);
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    const foundVacancy = vacancies.find((v) => v.vacancyId === parseInt(vacancyId));
    setVacancy(foundVacancy);
  }, [vacancyId, vacancies]);

  const copyInterviewLink = async () => {
    if (vacancy?.interviewLink) {
      try {
        await navigator.clipboard.writeText(vacancy.interviewLink);
        setLinkCopied(true);
        setTimeout(() => setLinkCopied(false), 2000); // Сброс через 2 секунды
      } catch (err) {
        console.error('Ошибка при копировании ссылки:', err);
        // Fallback для старых браузеров
        const textArea = document.createElement('textarea');
        textArea.value = vacancy.interviewLink;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setLinkCopied(true);
        setTimeout(() => setLinkCopied(false), 2000);
      }
    }
  };

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
      case 'aproved':
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
      case 'aproved':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getBusyTypeText = (busyType) => {
    switch (busyType) {
      case 'allTime':
        return 'Полная занятость';
      case 'projectTime':
        return 'Проектная занятость';
      default:
        return 'Не указано';
    }
  };

  if (!vacancy) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <h1 className='text-2xl font-semibold mb-4'>Вакансия не найдена</h1>
        <Button onClick={() => navigate('/applicant')}>Вернуться к списку</Button>
      </div>
    );
  }

  return (
    <div className='flex flex-col gap-[20px]'>
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
          Назад к списку вакансий
        </Button>
      </div>

      {/* Заголовок вакансии */}
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-[32px] font-bold text-gray-800 mb-2'>{vacancy.name}</h1>
          <p className='text-[18px] text-gray-600'>Банк ВТБ</p>
        </div>
        <Badge className={`px-4 py-2 text-lg font-medium ${getStatusColor(vacancy.status)}`}>
          {getStatusText(vacancy.status)}
        </Badge>
      </div>

      {/* Основная информация */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Основная информация</CardTitle>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Регион:</span>
              <span className='font-medium'>{vacancy.region}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Тип занятости:</span>
              <span className='font-medium'>{getBusyTypeText(vacancy.busyType)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Статус заявки:</span>
              <span className='font-medium'>{getStatusText(vacancy.status)}</span>
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
              <span className='font-medium'>{vacancy.hr?.name}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Email:</span>
              <span className='font-medium text-blue-600'>{vacancy.hr?.contact}</span>
            </div>
            {vacancy.interviewLink && (
              <div className='flex justify-between'>
                <span className='text-gray-600'>Ссылка на интервью:</span>
                <a
                  href={vacancy.interviewLink}
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

      {/* Описание вакансии */}
      {vacancy.description && (
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Описание вакансии</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-gray-700 leading-relaxed'>{vacancy.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Рекомендации по интервью */}
      {vacancy.interviewRecomendation && (
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Рекомендации по интервью</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-gray-700 leading-relaxed'>{vacancy.interviewRecomendation}</p>
          </CardContent>
        </Card>
      )}

      {/* Кнопки действий */}
      <div className='flex gap-4 justify-center flex-wrap'>
        {vacancy.status === 'rejected' ? (
          <Button className='bg-gray-500 hover:bg-gray-600 text-white px-8 py-3 text-lg' disabled>
            Заявка отклонена
          </Button>
        ) : vacancy.status === 'aproved' ? (
          <Button className='bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg'>Заявка одобрена</Button>
        ) : vacancy.status === 'interview' ? (
          <>
            <Button
              className='bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg'
              onClick={() => window.open(vacancy.interviewLink, '_blank')}
            >
              Пройти интервью
            </Button>
            <Button
              className={`px-8 py-3 text-lg ${linkCopied ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-purple-600 hover:bg-purple-700 text-white'}`}
              onClick={copyInterviewLink}
            >
              {linkCopied ? '✓ Ссылка скопирована!' : 'Получить ссылку на интервью'}
            </Button>
          </>
        ) : vacancy.interviewLink ? (
          <Button
            className='bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg'
            onClick={() => window.open(vacancy.interviewLink, '_blank')}
          >
            Пройти интервью
          </Button>
        ) : (
          <Button className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white px-8 py-3 text-lg'>Подать отклик</Button>
        )}

        {vacancy.status !== 'rejected' && vacancy.status !== 'aproved' && (
          <Button variant='outline' className='px-8 py-3 text-lg'>
            Сохранить в избранное
          </Button>
        )}
      </div>
    </div>
  );
};

export default ApplicantVacancyPage;
