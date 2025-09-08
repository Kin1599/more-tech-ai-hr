import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Badge} from '../../components/ui/badge';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Separator} from '../../components/ui/separator';
import {useStore} from '../../App/store';

const VacancyApplicantPage = () => {
  const {vacancyId, candidateId} = useParams();
  const navigate = useNavigate();
  const {vacancies, fetchHRApplicant} = useStore();

  const [applicant, setApplicant] = useState(null);
  const [vacancy, setVacancy] = useState(null);

  const interview = applicant?.interview;
  const cv = applicant?.cv;

  useEffect(() => {
    const loadData = async () => {
      // Находим вакансию
      const foundVacancy = vacancies.find((v) => v.vacancyId === parseInt(vacancyId));
      setVacancy(foundVacancy);

      // Загружаем данные кандидата
      if (candidateId && vacancyId) {
        try {
          const result = await fetchHRApplicant(parseInt(candidateId), parseInt(vacancyId));
          if (result.success) {
            setApplicant(result.data);
          } else {
            console.error('Ошибка при загрузке кандидата:', result.error);
          }
        } catch (error) {
          console.error('Ошибка при загрузке кандидата:', error);
        }
      }
    };
    loadData();
  }, [vacancyId, candidateId, vacancies, fetchHRApplicant]);

  // Функция для отображения статуса
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

  // Функция для получения цвета статуса
  const getStatusColor = (status) => {
    switch (status) {
      case 'rejected':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'cvReview':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'interview':
        return 'text-blue-600 bg-blue-100 border-blue-200';
      case 'waitResult':
        return 'text-purple-600 bg-purple-100 border-purple-200';
      case 'aproved':
        return 'text-green-600 bg-green-100 border-green-200';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  // Функция для отображения вердикта интервью
  const getVerdictText = (verdict) => {
    switch (verdict) {
      case 'strong_hire':
        return 'Сильная рекомендация к найму';
      case 'hire':
        return 'Рекомендация к найму';
      case 'no_hire':
        return 'Не рекомендуется к найму';
      case 'strong_no_hire':
        return 'Категорически не рекомендуется к найму';
      default:
        return 'Не определено';
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'strong_hire':
        return 'text-green-600 bg-green-100';
      case 'hire':
        return 'text-green-600 bg-green-100';
      case 'no_hire':
        return 'text-red-600 bg-red-100';
      case 'strong_no_hire':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (!applicant || !vacancy) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <h1 className='text-2xl font-semibold mb-4'>Кандидат не найден</h1>
        <Button onClick={() => navigate(`/hr/vacancy/${vacancyId}`)}>Вернуться к вакансии</Button>
      </div>
    );
  }

  return (
    <div className='flex flex-col gap-[10px]'>
      {/* Кнопка назад */}
      <div className='mb-4'>
        <Button
          onClick={() => navigate(`/hr/vacancy/${vacancyId}`)}
          variant='outline'
          className='flex items-center gap-2 cursor-pointer'
        >
          <svg className='w-4 h-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M15 19l-7-7 7-7' />
          </svg>
          Назад к вакансии
        </Button>
      </div>

      <div className='flex justify-between items-center'>
        <div className='text-[30px] font-bold'>Кандидат #{candidateId}</div>
        <div className='flex items-center gap-3'>
          <Badge className={`px-4 py-2 text-sm font-medium border shadow-sm ${getStatusColor(applicant.status)}`}>
            {getStatusText(applicant.status)}
          </Badge>
          {interview?.verdict && (
            <Badge className={`px-4 py-2 text-sm font-medium border shadow-sm ${getVerdictColor(interview.verdict)}`}>
              {getVerdictText(interview.verdict)}
            </Badge>
          )}
        </div>
      </div>
      {cv && cv.length > 0 && (
        <div className='space-y-4'>
          <h3 className='text-[20px] font-semibold'>Анализ резюме</h3>
          {cv.map((cvItem, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className='text-[18px]'>{cvItem.name}</CardTitle>
              </CardHeader>
              <CardContent className='space-y-3'>
                <div className='text-[16px]'>
                  <span className='font-bold'>Оценка: </span>
                  <span className='text-blue-600 font-semibold'>{cvItem.score.toFixed(2)}/100</span>
                </div>
                {cvItem.strengths && cvItem.strengths.length > 0 && (
                  <div>
                    <div className='font-bold text-green-600 mb-2'>Сильные стороны:</div>
                    <ul className='list-disc list-inside space-y-1'>
                      {cvItem.strengths.map((strength, idx) => (
                        <li key={idx} className='text-[14px]'>
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {cvItem.weaknesses && cvItem.weaknesses.length > 0 && (
                  <div>
                    <div className='font-bold text-red-600 mb-2'>Слабые стороны:</div>
                    <ul className='list-disc list-inside space-y-1'>
                      {cvItem.weaknesses.map((weakness, idx) => (
                        <li key={idx} className='text-[14px]'>
                          {weakness}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      {interview && (
        <div className='space-y-4'>
          <h3 className='text-[20px] font-semibold'>Результаты интервью</h3>
          <Card>
            <CardHeader>
              <CardTitle className='text-[18px]'>Общая информация</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4'>
              {interview.summary && (
                <div>
                  <div className='font-bold text-gray-700 mb-2'>Краткое резюме:</div>
                  <p className='text-[14px] text-gray-600 leading-relaxed'>{interview.summary}</p>
                </div>
              )}
              {interview.verdict && (
                <div>
                  <div className='font-bold text-gray-700 mb-2'>Вердикт:</div>
                  <Badge className={`px-3 py-1 text-sm font-medium ${getVerdictColor(interview.verdict)}`}>
                    {getVerdictText(interview.verdict)}
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {interview.strengths && interview.strengths.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className='text-[18px] text-green-600'>Сильные стороны</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className='list-disc list-inside space-y-1'>
                  {interview.strengths.map((strength, idx) => (
                    <li key={idx} className='text-[14px]'>
                      {strength}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {interview.weaknesses && interview.weaknesses.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className='text-[18px] text-red-600'>Слабые стороны</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className='list-disc list-inside space-y-1'>
                  {interview.weaknesses.map((weakness, idx) => (
                    <li key={idx} className='text-[14px]'>
                      {weakness}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {interview.recommendations && (
            <Card>
              <CardHeader>
                <CardTitle className='text-[18px] text-blue-600'>Рекомендации</CardTitle>
              </CardHeader>
              <CardContent>
                <p className='text-[14px] text-gray-600 leading-relaxed'>{interview.recommendations}</p>
              </CardContent>
            </Card>
          )}

          {interview.risk_notes && interview.risk_notes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className='text-[18px] text-orange-600'>Заметки о рисках</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className='list-disc list-inside space-y-1'>
                  {interview.risk_notes.map((risk, idx) => (
                    <li key={idx} className='text-[14px]'>
                      {risk}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default VacancyApplicantPage;
