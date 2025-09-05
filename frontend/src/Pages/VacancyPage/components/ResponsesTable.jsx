import React from 'react';
import {Avatar, AvatarImage, AvatarFallback} from '../../../components/ui/avatar';

const ResponsesTable = ({responses}) => {
  // Функция для отображения статуса
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

  // Функция для получения цвета статуса
  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'reviewed':
        return 'text-blue-600 bg-blue-100';
      case 'approved':
        return 'text-green-600 bg-green-100';
      case 'rejected':
        return 'text-red-600 bg-red-100';
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
          <div
            key={response.candidateId || index}
            className='flex justify-between items-center bg-white border border-solid border-[#303030] rounded-[20px] p-[20px] hover:bg-gray-50 transition-colors duration-200 text-[20px]'
          >
            {/* Кандидат */}
            <div style={{width: '400px'}} className='text-center truncate flex gap-[10px] items-center'>
              <Avatar className='w-[40px] h-[40px] cursor-pointer'>
                <AvatarImage alt='user' />
                <AvatarFallback>u</AvatarFallback>
              </Avatar>
              {response.candidateName}
            </div>

            {/* Оценка резюме */}
            <div style={{width: '200px'}} className='text-center truncate'>
              {response.cvScore}/100
            </div>

            {/* Статус */}
            <div style={{width: '200px'}} className='text-center truncate'>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(response.status)}`}>
                {getStatusText(response.status)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResponsesTable;
