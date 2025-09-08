import React from 'react';
import {useNavigate} from 'react-router-dom';
import {Badge} from '../../../components/ui/badge';
import {capitalizeFirst} from '../../../lib/utils';

const ApplicationCard = ({application}) => {
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/applicant/application/${application.vacancyId}`);
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

  const getBusyTypeColor = (busyType) => {
    switch (busyType) {
      case 'allTime':
        return 'bg-blue-100 text-blue-800';
      case 'partTime':
        return 'bg-green-100 text-green-800';
      case 'projectTime':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      className='flex items-start p-4 border rounded-lg w-[452px] h-[200px] cursor-pointer hover:bg-gray-50 hover:border-gray-300 hover:shadow-md transition-all duration-200'
      onClick={handleCardClick}
    >
      <div className='flex flex-col justify-between w-[100%] h-full'>
        <div className='flex justify-between items-start mb-4'>
          <div className='flex-1 mr-2'>
            <h3 className='text-[18px] font-semibold mb-1 line-clamp-2'>{capitalizeFirst(application.name)}</h3>
            <p className='text-gray-600 mb-1'>{capitalizeFirst(application.region)}</p>
          </div>
          <Badge className={getBusyTypeColor(application.busyType)}>{getBusyTypeText(application.busyType)}</Badge>
        </div>

        <div className='space-y-2'>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>HR-менеджер:</span>
            <span className='font-medium'>{capitalizeFirst(application.hr?.name) || 'Не указан'}</span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Контакт:</span>
            <span className='font-medium text-blue-600'>{application.hr?.contact || 'Не указан'}</span>
          </div>
          <div className='flex justify-between text-sm'>
            <span className='text-gray-600'>Статус:</span>
            <span className='font-medium text-green-600'>Отклик подан</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApplicationCard;
