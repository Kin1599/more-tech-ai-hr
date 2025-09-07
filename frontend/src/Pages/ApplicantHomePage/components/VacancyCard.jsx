import React from 'react';
import {useNavigate} from 'react-router-dom';
import {Badge} from '../../../components/ui/badge';

const VacancyCard = ({vacancy}) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/applicant/${vacancy.vacancyID}`);
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

  return (
    <div
      className='flex items-start p-4 border rounded-lg w-[452px] h-[240px] cursor-pointer hover:bg-gray-50 hover:border-gray-300 hover:shadow-md transition-all duration-200'
      onClick={handleCardClick}
    >
      <div className='flex flex-col justify-between w-[100%] h-full'>
        <div className='flex justify-between items-start mb-4'>
          <div>
            <h3 className='text-[18px] font-semibold mb-1'>{vacancy.name}</h3>
            <p className='text-gray-600 mb-1'>{vacancy.tribe || 'Банк ВТБ'}</p>
          </div>
          <Badge className={getStatusColor(vacancy.status)}>{getStatusText(vacancy.status)}</Badge>
        </div>

        <div className='space-y-2'>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Статус:</span>
            <span className='font-medium'>{getStatusText(vacancy.status)}</span>
          </div>
          {vacancy.otherInfo && (
            <div className='flex justify-between text-sm'>
              <span className='text-gray-600'>Доп. информация:</span>
              <span className='font-medium'>{vacancy.otherInfo}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VacancyCard;
