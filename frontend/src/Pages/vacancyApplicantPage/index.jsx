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
  const [isInterviewExpanded, setIsInterviewExpanded] = useState(true);
  const [isCVExpanded, setIsCVExpanded] = useState(true);

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
          {interview?.verdict && applicant?.status !== 'interview' && (
            <Badge className={`px-4 py-2 text-sm font-medium border shadow-sm ${getVerdictColor(interview.verdict)}`}>
              {getVerdictText(interview.verdict)}
            </Badge>
          )}
        </div>
      </div>
      {cv && cv.length > 0 && (
        <div className='space-y-4'>
          <Card>
            <CardHeader
              className='cursor-pointer hover:bg-gray-50 transition-colors duration-200'
              onClick={() => setIsCVExpanded(!isCVExpanded)}
            >
              <div className='flex items-center justify-between'>
                <CardTitle className='text-[18px]'>Анализ резюме</CardTitle>
                <div
                  className={`transform transition-transform duration-200 ${isCVExpanded ? 'rotate-180' : 'rotate-0'}`}
                >
                  <svg className='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                  </svg>
                </div>
              </div>
            </CardHeader>
            <div
              className={`overflow-hidden transition-all duration-300 ease-in-out ${
                isCVExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
              }`}
            >
              <CardContent className='space-y-6 pt-0'>
                {cv.map((cvItem, index) => (
                  <div key={index} className='space-y-3'>
                    <div className='flex items-center justify-between'>
                      <h4 className='text-[16px] font-semibold capitalize'>{cvItem.name}</h4>
                      <div className='text-[16px]'>
                        <span className='font-bold'>Оценка: </span>
                        <span className='text-blue-600 font-semibold'>{cvItem.score.toFixed(2)}/100</span>
                      </div>
                    </div>

                    <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
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
                    </div>

                    {index < cv.length - 1 && <Separator />}
                  </div>
                ))}
              </CardContent>
            </div>
          </Card>
        </div>
      )}
      {interview && (
        <div className='space-y-4'>
          <Card>
            <CardHeader
              className='cursor-pointer hover:bg-gray-50 transition-colors duration-200'
              onClick={() => setIsInterviewExpanded(!isInterviewExpanded)}
            >
              <div className='flex items-center justify-between'>
                <CardTitle className='text-[18px]'>Результаты интервью</CardTitle>
                <div
                  className={`transform transition-transform duration-200 ${isInterviewExpanded ? 'rotate-180' : 'rotate-0'}`}
                >
                  <svg className='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                  </svg>
                </div>
              </div>
            </CardHeader>
            <div
              className={`overflow-hidden transition-all duration-300 ease-in-out ${
                isInterviewExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
              }`}
            >
              <CardContent className='space-y-6 pt-0'>
                {/* Общая информация */}
                {(interview.summary || interview.verdict) && (
                  <div className='space-y-3'>
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
                  </div>
                )}

                {/* Разделитель если есть общая информация и оценка */}
                {(interview.summary || interview.verdict) &&
                  (interview.strengths?.length > 0 || interview.weaknesses?.length > 0) && <Separator />}

                {/* Оценка кандидата */}
                {(interview.strengths?.length > 0 || interview.weaknesses?.length > 0) && (
                  <div className='space-y-4'>
                    <h4 className='text-[16px] font-semibold'>Оценка кандидата</h4>
                    <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                      {interview.strengths && interview.strengths.length > 0 && (
                        <div>
                          <div className='font-bold text-green-600 mb-2'>Сильные стороны:</div>
                          <ul className='list-disc list-inside space-y-1'>
                            {interview.strengths.map((strength, idx) => (
                              <li key={idx} className='text-[14px]'>
                                {strength}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {interview.weaknesses && interview.weaknesses.length > 0 && (
                        <div>
                          <div className='font-bold text-red-600 mb-2'>Слабые стороны:</div>
                          <ul className='list-disc list-inside space-y-1'>
                            {interview.weaknesses.map((weakness, idx) => (
                              <li key={idx} className='text-[14px]'>
                                {weakness}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Разделитель если есть оценка и дополнительная информация */}
                {(interview.strengths?.length > 0 || interview.weaknesses?.length > 0) &&
                  (interview.recommendations || interview.risk_notes?.length > 0) && <Separator />}

                {/* Дополнительная информация */}
                {(interview.recommendations || interview.risk_notes?.length > 0) && (
                  <div className='space-y-4'>
                    <h4 className='text-[16px] font-semibold'>Дополнительная информация</h4>
                    <div className='space-y-4'>
                      {interview.recommendations && (
                        <div>
                          <div className='font-bold text-blue-600 mb-2'>Рекомендации:</div>
                          <p className='text-[14px] text-gray-600 leading-relaxed'>{interview.recommendations}</p>
                        </div>
                      )}
                      {interview.risk_notes && interview.risk_notes.length > 0 && (
                        <div>
                          <div className='font-bold text-orange-600 mb-2'>Заметки о рисках:</div>
                          <ul className='list-disc list-inside space-y-1'>
                            {interview.risk_notes.map((risk, idx) => (
                              <li key={idx} className='text-[14px]'>
                                {risk}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default VacancyApplicantPage;
