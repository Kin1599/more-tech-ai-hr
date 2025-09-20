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
  const [isExportingPDF, setIsExportingPDF] = useState(false);

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

  // Функция для экспорта в PDF
  const exportToPDF = async () => {
    setIsExportingPDF(true);
    try {
      const html2canvas = (await import('html2canvas')).default;
      const jsPDF = (await import('jspdf')).default;

      // Создаем простой HTML с правильной кодировкой
      const simpleHTML = `
        <!DOCTYPE html>
        <html lang="ru">
        <head>
          <meta charset="UTF-8">
          <style>
            body { font-family: Arial, sans-serif; background: white; color: black; padding: 20px; max-width: 800px; margin: 0; line-height: 1.6; }
            h1 { color: #333; margin-bottom: 20px; font-size: 24px; }
            h2 { color: #555; margin-bottom: 10px; font-size: 18px; }
            h3 { color: #666; margin-bottom: 8px; font-size: 16px; }
            .section { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
            .cv-item { margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .cv-item:last-child { border-bottom: none; }
            ul { margin: 5px 0; padding-left: 20px; }
            li { margin-bottom: 3px; }
            strong { font-weight: bold; }
          </style>
        </head>
        <body>
          <h1>Информация о кандидате</h1>
          
          <div class="section">
            <h2>Личная информация</h2>
            <p><strong>Имя:</strong> ${applicant?.name || 'Не указано'}</p>
            <p><strong>Email:</strong> ${applicant?.email || 'Не указано'}</p>
            <p><strong>Телефон:</strong> ${applicant?.phone || 'Не указано'}</p>
            <p><strong>Статус:</strong> ${getStatusText(applicant?.status) || 'Не указано'}</p>
          </div>

          ${
            cv && cv.length > 0
              ? `
            <div class="section">
              <h2>Анализ резюме</h2>
              ${cv
                .map(
                  (cvItem, index) => `
                <div class="cv-item">
                  <h3>${cvItem.name || 'Навык'}</h3>
                  <p><strong>Оценка:</strong> ${cvItem.score || '0'}/100</p>
                  ${
                    cvItem.strengths && cvItem.strengths.length > 0
                      ? `
                    <div>
                      <strong>Сильные стороны:</strong>
                      <ul>
                        ${cvItem.strengths.map((strength) => `<li>${strength}</li>`).join('')}
                      </ul>
                    </div>
                  `
                      : ''
                  }
                  ${
                    cvItem.weaknesses && cvItem.weaknesses.length > 0
                      ? `
                    <div>
                      <strong>Слабые стороны:</strong>
                      <ul>
                        ${cvItem.weaknesses.map((weakness) => `<li>${weakness}</li>`).join('')}
                      </ul>
                    </div>
                  `
                      : ''
                  }
                </div>
              `
                )
                .join('')}
            </div>
          `
              : ''
          }

          ${
            interview
              ? `
            <div class="section">
              <h2>Итоговый результат собеседования</h2>
              ${interview.verdict ? `<p><strong>Итоговое решение:</strong> ${getVerdictText(interview.verdict)}</p>` : ''}
              ${interview.summary ? `<p><strong>Краткое резюме:</strong> ${interview.summary}</p>` : ''}
              ${
                interview.strengths && interview.strengths.length > 0
                  ? `
                <div>
                  <strong>Сильные стороны:</strong>
                  <ul>
                    ${interview.strengths.map((strength) => `<li>${strength}</li>`).join('')}
                  </ul>
                </div>
              `
                  : ''
              }
              ${
                interview.weaknesses && interview.weaknesses.length > 0
                  ? `
                <div>
                  <strong>Области для развития:</strong>
                  <ul>
                    ${interview.weaknesses.map((weakness) => `<li>${weakness}</li>`).join('')}
                  </ul>
                </div>
              `
                  : ''
              }
              ${interview.recommendations ? `<p><strong>Рекомендации:</strong> ${interview.recommendations}</p>` : ''}
              ${
                interview.risk_notes && interview.risk_notes.length > 0
                  ? `
                <div>
                  <strong>Заметки о рисках:</strong>
                  <ul>
                    ${interview.risk_notes.map((risk) => `<li>${risk}</li>`).join('')}
                  </ul>
                </div>
              `
                  : ''
              }
            </div>
          `
              : ''
          }
        </body>
        </html>
      `;

      // Создаем временный iframe для рендеринга HTML
      const iframe = document.createElement('iframe');
      iframe.style.position = 'absolute';
      iframe.style.left = '-9999px';
      iframe.style.top = '0';
      iframe.style.width = '800px';
      iframe.style.height = '600px';
      iframe.style.border = 'none';

      document.body.appendChild(iframe);

      // Ждем загрузки iframe
      await new Promise((resolve) => {
        iframe.onload = resolve;
        iframe.srcdoc = simpleHTML;
      });

      // Даем время на рендеринг
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Создаем canvas из iframe
      const canvas = await html2canvas(iframe.contentDocument.body, {
        scale: 1.5,
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
        allowTaint: true,
      });

      // Удаляем iframe
      document.body.removeChild(iframe);

      // Создаем PDF
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');

      const imgWidth = 210; // A4 ширина в мм
      const pageHeight = 295; // A4 высота в мм
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      // Добавляем первую страницу
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      // Добавляем дополнительные страницы если нужно
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      // Скачиваем PDF
      const fileName = `candidate_${candidateId}_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);
    } catch (error) {
      console.error('Ошибка при экспорте в PDF:', error);
      alert('Ошибка при создании PDF файла. Попробуйте обновить страницу и повторить попытку.');
    } finally {
      setIsExportingPDF(false);
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
      {/* Кнопки управления */}
      <div className='mb-4 flex justify-between items-center'>
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

        <Button
          onClick={exportToPDF}
          disabled={isExportingPDF}
          className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white flex items-center gap-2'
        >
          {isExportingPDF ? (
            <>
              <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-white'></div>
              Создание PDF...
            </>
          ) : (
            <>
              <svg className='w-4 h-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth={2}
                  d='M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
                />
              </svg>
              Экспорт в PDF
            </>
          )}
        </Button>
      </div>

      <div id='candidate-content' className='space-y-6'>
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
        <div className='space-y-4'>
            <Card>
              <CardHeader
                className='cursor-pointer hover:bg-gray-50 transition-colors duration-200'
                onClick={() => setIsInterviewExpanded(!isInterviewExpanded)}
              >
                <div className='flex items-center justify-between'>
                  <CardTitle className='text-[18px]'>Итоговый результат собеседования</CardTitle>
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
                  {/* Итоговый вердикт - выделяем его особо */}
                  {interview.verdict && interview.verdict !== 'no_hire' ? (
                    <div className='bg-gray-50 p-4 rounded-lg border-2 border-gray-200'>
                      <div className='flex items-center justify-between mb-3'>
                        <h3 className='text-lg font-bold text-gray-800'>Итоговое решение</h3>
                        <Badge className={`px-4 py-2 text-base font-semibold ${getVerdictColor(interview.verdict)}`}>
                          {getVerdictText(interview.verdict)}
                        </Badge>
                      </div>
                      {interview.summary && interview.summary !== "Интервью ещё не проведено" && (
                        <p className='text-[14px] text-gray-700 leading-relaxed'>{interview.summary}</p>
                      )}
                    </div>
                  ) : (
                    <div className='bg-yellow-50 p-4 rounded-lg border-2 border-yellow-200'>
                      <div className='flex items-center mb-3'>
                        <svg className='w-6 h-6 text-yellow-600 mr-3' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                          <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' />
                        </svg>
                        <h3 className='text-lg font-bold text-yellow-800'>Ожидание собеседования</h3>
                      </div>
                      <p className='text-[14px] text-yellow-700 leading-relaxed'>
                        Собеседование ещё не проведено. Результаты будут доступны после завершения интервью.
                      </p>
                    </div>
                  )}

                  {/* Разделитель */}
                  {interview.verdict && interview.verdict !== 'no_hire' &&
                    (interview.strengths?.length > 0 || interview.weaknesses?.length > 0) && <Separator />}

                  {/* Детальная оценка кандидата */}
                  {interview.verdict && interview.verdict !== 'no_hire' && 
                   (interview.strengths?.length > 0 || interview.weaknesses?.length > 0) && (
                    <div className='space-y-4'>
                      <h4 className='text-[16px] font-semibold text-gray-800'>Детальная оценка</h4>
                      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                        {interview.strengths && interview.strengths.length > 0 && (
                          <div className='bg-green-50 p-4 rounded-lg border border-green-200'>
                            <div className='flex items-center mb-3'>
                              <svg className='w-5 h-5 text-green-600 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                              </svg>
                              <div className='font-bold text-green-700'>Сильные стороны</div>
                            </div>
                            <ul className='space-y-2'>
                              {interview.strengths.map((strength, idx) => (
                                <li key={idx} className='text-[14px] text-green-800 flex items-start'>
                                  <span className='text-green-600 mr-2'>•</span>
                                  {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {interview.weaknesses && interview.weaknesses.length > 0 && (
                          <div className='bg-red-50 p-4 rounded-lg border border-red-200'>
                            <div className='flex items-center mb-3'>
                              <svg className='w-5 h-5 text-red-600 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z' />
                              </svg>
                              <div className='font-bold text-red-700'>Области для развития</div>
                            </div>
                            <ul className='space-y-2'>
                              {interview.weaknesses.map((weakness, idx) => (
                                <li key={idx} className='text-[14px] text-red-800 flex items-start'>
                                  <span className='text-red-600 mr-2'>•</span>
                                  {weakness}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Разделитель */}
                  {interview.verdict && interview.verdict !== 'no_hire' &&
                    (interview.strengths?.length > 0 || interview.weaknesses?.length > 0) &&
                    (interview.recommendations || interview.risk_notes?.length > 0) && <Separator />}

                  {/* Рекомендации и дополнительные заметки */}
                  {interview.verdict && interview.verdict !== 'no_hire' && 
                   (interview.recommendations || interview.risk_notes?.length > 0) && (
                    <div className='space-y-4'>
                      <h4 className='text-[16px] font-semibold text-gray-800'>Рекомендации и заметки</h4>
                      <div className='space-y-4'>
                        {interview.recommendations && (
                          <div className='bg-blue-50 p-4 rounded-lg border border-blue-200'>
                            <div className='flex items-center mb-3'>
                              <svg className='w-5 h-5 text-blue-600 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' />
                              </svg>
                              <div className='font-bold text-blue-700'>Рекомендации</div>
                            </div>
                            <p className='text-[14px] text-blue-800 leading-relaxed'>{interview.recommendations}</p>
                          </div>
                        )}
                        {interview.risk_notes && interview.risk_notes.length > 0 && (
                          <div className='bg-orange-50 p-4 rounded-lg border border-orange-200'>
                            <div className='flex items-center mb-3'>
                              <svg className='w-5 h-5 text-orange-600 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z' />
                              </svg>
                              <div className='font-bold text-orange-700'>Заметки о рисках</div>
                            </div>
                            <ul className='space-y-2'>
                              {interview.risk_notes.map((risk, idx) => (
                                <li key={idx} className='text-[14px] text-orange-800 flex items-start'>
                                  <span className='text-orange-600 mr-2'>•</span>
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
      </div>
    </div>
  );
};

export default VacancyApplicantPage;
