import React from 'react';
import {Link} from 'react-router-dom';
import {Avatar, AvatarImage, AvatarFallback} from '../../../components/ui/avatar';
import arrowIcon from '../../../Shared/imgs/arrow-right.svg';

const ResponsesTable = ({responses, vacancyId}) => {
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
        return 'text-red-600 bg-red-100';
      case 'cvReview':
        return 'text-yellow-600 bg-yellow-100';
      case 'interview':
        return 'text-blue-600 bg-blue-100';
      case 'waitResult':
        return 'text-purple-600 bg-purple-100';
      case 'aproved':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Заголовки таблицы
  const headers = [
    {name: 'Кандидат', width: '400px'},
    {name: 'Оценка резюме', width: '200px'},
    {name: 'Статус', width: '200px'},
  ];

  if (!responses || responses.length === 0) {
    return <div className='text-center py-8 text-gray-500 text-[20px]'>Откликов пока нет</div>;
  }

  return (
    <div className='flex flex-col gap-[20px]'>
      {/* Заголовки таблицы */}
      <div className='flex justify-between items-center p-[20px] pb-0 pt-0 font-bold text-[24px]'>
        {headers.map((header) => (
          <div key={header.name} style={{width: header.width}} className='text-center truncate'>
            {header.name}
          </div>
        ))}
      </div>

      {/* Строки таблицы */}
      <div className='flex flex-col gap-[10px]'>
        {responses.map((response, index) => (
          <Link
            key={response.applicantId || index}
            to={`/hr/vacancy/${vacancyId}/candidate/${response.applicantId}`}
            className='flex justify-between items-center bg-white border border-solid border-[#303030] rounded-[20px] p-[20px] hover:bg-[#eb5e28] hover:text-white transition-colors duration-200 cursor-pointer group text-[20px]'
          >
            {/* Кандидат */}
            <div style={{width: '400px'}} className='text-center truncate flex gap-[10px] items-center'>
              <Avatar className='w-[40px] h-[40px] cursor-pointer'>
                <AvatarImage alt='user' />
                <AvatarFallback>u</AvatarFallback>
              </Avatar>
              {response.name}
            </div>

            {/* Оценка резюме */}
            <div style={{width: '200px'}} className='text-center truncate'>
              {response.score}/100
            </div>

            {/* Статус */}
            <div style={{width: '200px'}} className='text-center truncate'>
              <div className='group-hover:hidden'>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(response.status)}`}>
                  {getStatusText(response.status)}
                </span>
              </div>
              <div className='hidden group-hover:flex items-center gap-[10px]'>
                Перейти <img src={arrowIcon} alt='Перейти' className='w-[30px] h-[30px]'></img>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default ResponsesTable;
