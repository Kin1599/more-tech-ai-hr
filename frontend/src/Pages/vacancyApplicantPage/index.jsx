import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Badge} from '../../components/ui/badge';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {Separator} from '../../components/ui/separator';
import {useStore} from '../../App/Store';

const VacancyApplicantPage = () => {
  const {vacancyId, candidateId} = useParams();
  const navigate = useNavigate();
  const {vacancies} = useStore();

  const [applicant, setApplicant] = useState(null);
  const [vacancy, setVacancy] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    summary: false,
    recommendations: false,
    risks: false,
  });

  const interview = applicant?.interview;
  const cv = applicant?.cv;

  // Функция для переключения аккордеона
  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  useEffect(() => {
    // Находим вакансию
    const foundVacancy = vacancies.find((v) => v.vacancyId === parseInt(vacancyId));
    setVacancy(foundVacancy);

    // Пока кандидаты не реализованы - используем null
    setApplicant(null);
  }, [vacancyId, candidateId, vacancies]);

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

  // Функция для отображения вердикта интервью
  const getVerdictText = (verdict) => {
    switch (verdict) {
      case 'strong_hire':
        return 'Сильно рекомендован к найму';
      case 'hire':
        return 'Рекомендован к найму';
      case 'borderline':
        return 'Пограничный случай';
      case 'no_hire':
        return 'Не рекомендован к найму';
      default:
        return 'Не определен';
    }
  };

  // Функция для получения цвета вердикта
  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'strong_hire':
        return 'bg-green-100 text-green-800';
      case 'hire':
        return 'bg-blue-100 text-blue-800';
      case 'borderline':
        return 'bg-yellow-100 text-yellow-800';
      case 'no_hire':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
        <div className='text-[30px] font-bold'>{applicant.candidateName}</div>
        {applicant.verdict && (
          <Badge className={`px-4 py-2 text-lg font-medium ${getVerdictColor(applicant.verdict)}`}>
            {getVerdictText(applicant.verdict)}
          </Badge>
        )}
      </div>

      <div className='text-[16px]'>
        <span className='font-bold'>Статус: </span>
        <span>{getStatusText(applicant.status)}</span>
      </div>
      <div className='text-[16px]'>
        <span className='font-bold'>Общая оценка резюме: </span>
        <span>{applicant.cvScore} баллов</span>
      </div>
      {cv?.strengths && (
        <div className='text-[16px]'>
          <span className='font-bold'>Сильные стороны резьюме: </span>
          {cv?.strengths.map((strength, index) => (
            <span key={strength}>
              {strength}
              {index !== cv?.strengths.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}
      {cv?.weaknesses && (
        <div className='text-[16px]'>
          <span className='font-bold'>Слабые стороны резьюме: </span>
          {cv?.weaknesses.map((weakness, index) => (
            <span key={weakness}>
              {weakness}
              {index !== cv?.weaknesses.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}
      {interview?.strengths && (
        <div className='text-[16px]'>
          <span className='font-bold'>Сильные стороны интервью: </span>
          {interview?.strengths.map((strength, index) => (
            <span key={strength}>
              {strength}
              {index !== interview?.strengths.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}
      {interview?.weaknesses && (
        <div className='text-[16px]'>
          <span className='font-bold'>Слабые стороны интервью: </span>
          {interview?.weaknesses.map((weakness, index) => (
            <span key={weakness}>
              {weakness}
              {index !== interview?.weaknesses.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}
      {interview?.summary && (
        <div>
          <div
            className='flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors duration-200 p-4 rounded-lg border border-gray-200'
            onClick={() => toggleSection('summary')}
          >
            <h3 className='text-[24px] font-semibold'>Выдержка из интервью</h3>
            <div
              className={`transform transition-transform duration-300 ease-in-out ${expandedSections.summary ? 'rotate-180' : 'rotate-0'}`}
            >
              <svg className='w-5 h-5 text-gray-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
              </svg>
            </div>
          </div>
          <div
            className={`overflow-hidden transition-all duration-300 ease-in-out ${
              expandedSections.summary ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
            }`}
          >
            <Card className='mt-2'>
              <CardContent className='p-4'>
                <p className='text-gray-700'>{interview.summary}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {interview?.recommendations && (
        <div>
          <div
            className='flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors duration-200 p-4 rounded-lg border border-gray-200'
            onClick={() => toggleSection('recommendations')}
          >
            <h3 className='text-[24px] font-semibold'>Рекомендации</h3>
            <div
              className={`transform transition-transform duration-300 ease-in-out ${expandedSections.recommendations ? 'rotate-180' : 'rotate-0'}`}
            >
              <svg className='w-5 h-5 text-gray-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
              </svg>
            </div>
          </div>
          <div
            className={`overflow-hidden transition-all duration-300 ease-in-out ${
              expandedSections.recommendations ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
            }`}
          >
            <Card className='mt-2'>
              <CardContent className='p-4'>
                <p className='text-gray-700'>{interview.recommendations}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {interview?.risk_notes && interview.risk_notes.length > 0 && (
        <div>
          <div
            className='flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors duration-200 p-4 rounded-lg border border-gray-200'
            onClick={() => toggleSection('risks')}
          >
            <h3 className='text-[24px] font-semibold'>Риски</h3>
            <div
              className={`transform transition-transform duration-300 ease-in-out ${expandedSections.risks ? 'rotate-180' : 'rotate-0'}`}
            >
              <svg className='w-5 h-5 text-gray-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
              </svg>
            </div>
          </div>
          <div
            className={`overflow-hidden transition-all duration-300 ease-in-out ${
              expandedSections.risks ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
            }`}
          >
            <Card className='mt-2'>
              <CardContent className='p-4 space-y-2'>
                {interview.risk_notes.map((risk, index) => (
                  <div key={index} className='p-3 bg-orange-50 border-l-4 border-orange-400 rounded'>
                    <p className='text-gray-700'>{risk}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default VacancyApplicantPage;
