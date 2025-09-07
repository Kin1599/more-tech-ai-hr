import React from 'react';
import {useNavigate} from 'react-router-dom';
import {Badge} from '../../../components/ui/badge';

const VacancyCard = ({vacancy}) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/applicant/${vacancy.vacancyId}`);
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'На рассмотрении';
      case 'reviewed':
        return 'Просмотрено';
      case 'approved':
        return 'Одобрено';
      case 'rejected':
        return 'Отклонено';
      default:
        return 'Неизвестно';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'reviewed':
        return 'bg-blue-100 text-blue-800';
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
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

  return (
    <div
      className='flex items-start p-4 border rounded-lg w-[452px] h-[240px] cursor-pointer hover:bg-gray-50 hover:border-gray-300 hover:shadow-md transition-all duration-200'
      onClick={handleCardClick}
    >
      <div className='flex flex-col justify-between w-[100%] h-full'>
        <div className='flex justify-between items-start mb-4'>
          <div>
            <h3 className='text-[18px] font-semibold mb-1'>{vacancy.name}</h3>
            <p className='text-gray-600 mb-1'>Банк ВТБ</p>
          </div>
          <Badge className={getStatusColor(vacancy.status)}>{getStatusText(vacancy.status)}</Badge>
        </div>

        <div className='space-y-2'>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Регион:</span>
            <span className='font-medium'>{vacancy.region}</span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Тип занятости:</span>
            <span className='font-medium'>{getBusyTypeText(vacancy.busyType)}</span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>HR:</span>
            <span className='font-medium'>{vacancy.hr?.name}</span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Дата отклика:</span>
            <span className='font-medium'>{vacancy.applicationDate}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VacancyCard;
