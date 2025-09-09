import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Badge} from '../../components/ui/badge';
import {Card, CardContent, CardHeader, CardTitle} from '../../components/ui/card';
import {useStore} from '../../App/store';
import {capitalizeFirst} from '../../lib/utils';

const ApplicantVacancyPage = () => {
  const {vacancyId} = useParams();
  const navigate = useNavigate();
  const {fetchApplicantVacancy, applyToVacancy, successToast, errorToast} = useStore();

  const [vacancy, setVacancy] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [applicationStatus, setApplicationStatus] = useState(null); // 'applied', 'error', null

  useEffect(() => {
    const loadVacancy = async () => {
      if (vacancyId) {
        setIsLoading(true);
        try {
          const result = await fetchApplicantVacancy(parseInt(vacancyId));
          if (result.success) {
            setVacancy(result.data);
          } else {
            console.error('Ошибка при загрузке вакансии:', result.error);
          }
        } catch (error) {
          console.error('Ошибка при загрузке вакансии:', error);
        } finally {
          setIsLoading(false);
        }
      }
    };
    loadVacancy();
  }, [vacancyId, fetchApplicantVacancy]);

  const handleApplyToVacancy = async () => {
    if (!vacancyId || isApplying) return;

    setIsApplying(true);
    setApplicationStatus(null);

    try {
      const result = await applyToVacancy(parseInt(vacancyId));
      if (result.success) {
        setApplicationStatus('applied');
        successToast('Отклик подан', 'Отклик успешно подан! Мы свяжемся с вами в ближайшее время.');
      } else {
        setApplicationStatus('error');
        errorToast('Ошибка', result.error || 'Ошибка при подаче отклика. Попробуйте позже.');
      }
    } catch {
      setApplicationStatus('error');
      errorToast('Ошибка', 'Ошибка при подаче отклика. Проверьте подключение к интернету.');
    } finally {
      setIsApplying(false);
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active':
        return 'Активная';
      case 'inactive':
        return 'Неактивная';
      case 'closed':
        return 'Закрыта';
      default:
        return 'Неизвестно';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'closed':
        return 'bg-red-100 text-red-800';
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

  const getOfferTypeText = (offerType) => {
    switch (offerType) {
      case 'TK':
        return 'Трудовой договор';
      case 'GPC':
        return 'ГПХ';
      case 'IP':
        return 'ИП';
      default:
        return 'Не указано';
    }
  };

  const formatSalary = (min, max) => {
    if (min && max) {
      return `${min.toLocaleString()} - ${max.toLocaleString()} ₽`;
    } else if (min) {
      return `от ${min.toLocaleString()} ₽`;
    } else if (max) {
      return `до ${max.toLocaleString()} ₽`;
    }
    return 'Не указана';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
  };

  if (isLoading) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28] mb-4'></div>
        <h1 className='text-2xl font-semibold mb-4'>Загрузка вакансии...</h1>
      </div>
    );
  }

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
      {/* Кнопка назад и действия */}
      <div className='flex justify-between items-center'>
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

        {/* Кнопки действий */}
        {vacancy.status === 'closed' ? (
          <Button className='bg-gray-500 hover:bg-gray-600 text-white px-8 py-3 text-lg' disabled>
            Вакансия закрыта
          </Button>
        ) : vacancy.status === 'inactive' ? (
          <Button className='bg-gray-500 hover:bg-gray-600 text-white px-8 py-3 text-lg' disabled>
            Вакансия неактивна
          </Button>
        ) : applicationStatus === 'applied' ? (
          <Button className='bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg' disabled>
            ✓ Отклик подан
          </Button>
        ) : applicationStatus === 'error' ? (
          <div className='flex flex-col items-end gap-2'>
            <Button
              className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white px-8 py-3 text-lg'
              onClick={handleApplyToVacancy}
              disabled={isApplying}
            >
              {isApplying ? 'Подача отклика...' : 'Попробовать снова'}
            </Button>
            <p className='text-sm text-red-600'>Ошибка при подаче отклика</p>
          </div>
        ) : (
          <div className='flex gap-3'>
            <Button
              className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white px-8 py-3 text-lg cursor-pointer'
              onClick={handleApplyToVacancy}
              disabled={isApplying}
            >
              {isApplying ? 'Подача отклика...' : 'Подать отклик'}
            </Button>
            <Button variant='outline' className='px-8 py-3 text-lg'>
              Сохранить в избранное
            </Button>
          </div>
        )}
      </div>

      {/* Заголовок вакансии */}
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-[32px] font-bold text-gray-800 mb-2'>{capitalizeFirst(vacancy.name)}</h1>
          <p className='text-[18px] text-gray-600'>{capitalizeFirst(vacancy.department) || 'Банк ВТБ'}</p>
          <p className='text-sm text-gray-500'>
            {capitalizeFirst(vacancy.city)}, {capitalizeFirst(vacancy.region)}
          </p>
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
              <span className='font-medium'>{capitalizeFirst(vacancy.region)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Город:</span>
              <span className='font-medium'>{capitalizeFirst(vacancy.city)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Тип занятости:</span>
              <span className='font-medium'>{getBusyTypeText(vacancy.busyType)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Тип договора:</span>
              <span className='font-medium'>{getOfferTypeText(vacancy.offerType)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Зарплата:</span>
              <span className='font-medium'>{formatSalary(vacancy.salaryMin, vacancy.salaryMax)}</span>
            </div>
            {vacancy.annualBonus > 0 && (
              <div className='flex justify-between'>
                <span className='text-gray-600'>Годовой бонус:</span>
                <span className='font-medium'>{vacancy.annualBonus.toLocaleString()} ₽</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Дополнительная информация</CardTitle>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Дата публикации:</span>
              <span className='font-medium'>{formatDate(vacancy.date)}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Опыт работы:</span>
              <span className='font-medium'>{vacancy.exp > 0 ? `${vacancy.exp} лет` : 'Без опыта'}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Образование:</span>
              <span className='font-medium'>{vacancy.degree ? 'Высшее' : 'Не требуется'}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>Командировки:</span>
              <span className='font-medium'>{vacancy.businessTrips ? 'Да' : 'Нет'}</span>
            </div>
            {vacancy.address && (
              <div className='flex justify-between'>
                <span className='text-gray-600'>Адрес:</span>
                <span className='font-medium'>{vacancy.address}</span>
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

      {/* Требования к кандидату */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        {vacancy.computerSkills && (
          <Card>
            <CardHeader>
              <CardTitle className='text-[20px] font-semibold'>Компьютерные навыки</CardTitle>
            </CardHeader>
            <CardContent>
              <p className='text-gray-700 leading-relaxed'>{vacancy.computerSkills}</p>
            </CardContent>
          </Card>
        )}

        {vacancy.specialSoftware && (
          <Card>
            <CardHeader>
              <CardTitle className='text-[20px] font-semibold'>Специальное ПО</CardTitle>
            </CardHeader>
            <CardContent>
              <p className='text-gray-700 leading-relaxed'>{vacancy.specialSoftware}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Языковые требования */}
      {vacancy.foreignLanguages && (
        <Card>
          <CardHeader>
            <CardTitle className='text-[20px] font-semibold'>Иностранные языки</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='space-y-2'>
              <p className='text-gray-700'>
                <strong>Языки:</strong> {vacancy.foreignLanguages}
              </p>
              {vacancy.languageLevel && (
                <p className='text-gray-700'>
                  <strong>Уровень:</strong> {vacancy.languageLevel}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ApplicantVacancyPage;
