import React from 'react';
import {useNavigate} from 'react-router-dom';
import {Badge} from '../../../components/ui/badge';
import {capitalizeFirst} from '../../../lib/utils';

const VacancyCard = ({vacancy}) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/applicant/${vacancy.vacancyId}`);
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

  return (
    <div
      className='flex items-start p-4 border rounded-lg w-[452px] h-[240px] cursor-pointer hover:bg-gray-50 hover:border-gray-300 hover:shadow-md transition-all duration-200'
      onClick={handleCardClick}
    >
      <div className='flex flex-col justify-between w-[100%] h-full'>
        <div className='flex justify-between items-start mb-4'>
          <div className='flex-1 mr-2'>
            <h3 className='text-[18px] font-semibold mb-1 line-clamp-2'>{capitalizeFirst(vacancy.name)}</h3>
            <p className='text-gray-600 mb-1'>{capitalizeFirst(vacancy.department) || 'Банк ВТБ'}</p>
            <p className='text-sm text-gray-500'>
              {capitalizeFirst(vacancy.city)}, {capitalizeFirst(vacancy.region)}
            </p>
          </div>
          <Badge className={getStatusColor(vacancy.status)}>{getStatusText(vacancy.status)}</Badge>
        </div>

        <div className='space-y-2'>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Зарплата:</span>
            <span className='font-medium'>{formatSalary(vacancy.salaryMin, vacancy.salaryMax)}</span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Тип занятости:</span>
            <span className='font-medium'>
              {vacancy.busyType === 'allTime'
                ? 'Полная'
                : vacancy.busyType === 'partTime'
                  ? 'Частичная'
                  : vacancy.busyType}
            </span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Дата:</span>
            <span className='font-medium'>{formatDate(vacancy.date)}</span>
          </div>
          {vacancy.exp > 0 && (
            <div className='flex justify-between text-sm'>
              <span className='text-gray-600'>Опыт:</span>
              <span className='font-medium'>{vacancy.exp} лет</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VacancyCard;
