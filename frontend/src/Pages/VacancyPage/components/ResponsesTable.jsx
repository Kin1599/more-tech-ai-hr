import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import {Avatar, AvatarImage, AvatarFallback} from '../../../components/ui/avatar';
import arrowIcon from '../../../Shared/imgs/arrow-right.svg';

/**
 * Компонент таблицы откликов с функциональностью тестирования пиктограмм схожести
 * 
 * Для тестирования пиктограмм схожести через Developer Tools используйте:
 * - showAllSimilarityIcons() - показать все пиктограммы
 * - hideAllSimilarityIcons() - скрыть все пиктограммы  
 * - toggleSimilarityIcon(applicantId, show, similarId) - управление конкретной пиктограммой
 * 
 * Пример: showAllSimilarityIcons() в консоли браузера
 */

const ResponsesTable = ({responses, vacancyId}) => {
  const [hoveredSimilarId, setHoveredSimilarId] = useState(null);

  // Функция для тестирования пиктограммы схожести через developer tools
  React.useEffect(() => {
    // Добавляем глобальную функцию для тестирования
    window.toggleSimilarityIcon = (applicantId, show = true, similarId = 999) => {
      const element = document.querySelector(`[data-testid="similarity-icon-${applicantId}"]`);
      if (element) {
        const parent = element.closest('[data-testid^="response-row-"]');
        if (parent) {
          // Находим элемент схожести в этой строке
          const similarityContainer = parent.querySelector('[data-testid^="similarity-container-"]');
          if (similarityContainer) {
            similarityContainer.innerHTML = show ? `
              <div 
                class="flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 hover:bg-orange-200 transition-colors relative cursor-help"
                title="Тестовая пиктограмма схожести"
              >
                <svg 
                  class="w-5 h-5 text-orange-600" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path 
                    fill-rule="evenodd" 
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" 
                    clip-rule="evenodd" 
                  />
                </svg>
              </div>
            ` : '<span class="text-gray-400">—</span>';
          }
        }
      }
    };

    // Функция для показа всех пиктограмм схожести
    window.showAllSimilarityIcons = () => {
      const containers = document.querySelectorAll('[data-testid^="similarity-container-"]');
      containers.forEach((container, index) => {
        container.innerHTML = `
          <div 
            class="flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 hover:bg-orange-200 transition-colors relative cursor-help"
            title="Тестовая пиктограмма схожести для кандидата ${index + 1}"
          >
            <svg 
              class="w-5 h-5 text-orange-600" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fill-rule="evenodd" 
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" 
                clip-rule="evenodd" 
              />
            </svg>
          </div>
        `;
      });
    };

    // Функция для скрытия всех пиктограмм схожести
    window.hideAllSimilarityIcons = () => {
      const containers = document.querySelectorAll('[data-testid^="similarity-container-"]');
      containers.forEach(container => {
        container.innerHTML = '<span class="text-gray-400">—</span>';
      });
    };

    // Добавляем информацию в консоль для разработчиков
    console.log('🔧 Функции для тестирования схожести резюме:');
    console.log('toggleSimilarityIcon(applicantId, show, similarId) - показать/скрыть пиктограмму для конкретного кандидата');
    console.log('showAllSimilarityIcons() - показать все пиктограммы схожести');
    console.log('hideAllSimilarityIcons() - скрыть все пиктограммы схожести');
    console.log('');
    console.log('Примеры использования:');
    console.log('toggleSimilarityIcon(1, true, 999) - показать пиктограмму для кандидата с ID 1');
    console.log('toggleSimilarityIcon(1, false) - скрыть пиктограмму для кандидата с ID 1');
    console.log('showAllSimilarityIcons() - показать все пиктограммы сразу');
    console.log('hideAllSimilarityIcons() - скрыть все пиктограммы');

    return () => {
      // Очищаем глобальные функции при размонтировании
      delete window.toggleSimilarityIcon;
      delete window.showAllSimilarityIcons;
      delete window.hideAllSimilarityIcons;
    };
  }, []);

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
    {name: 'Кандидат', width: '350px'},
    {name: 'Оценка резюме', width: '180px'},
    {name: 'Статус', width: '180px'},
    {name: 'Проверен', width: '120px'},
    {name: 'Схожесть', width: '100px'},
  ];

  if (!responses || responses.length === 0) {
    return <div className='text-center py-8 text-gray-500 text-[20px]'>Откликов пока нет</div>;
  }

  return (
    <div className='flex flex-col gap-[20px]'>
      {/* Заголовки таблицы */}
      <div className='flex justify-between items-center p-[20px] pb-0 pt-0 font-bold text-[18px]'>
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
            className='flex justify-between items-center bg-white border border-solid border-[#303030] rounded-[20px] p-[20px] hover:bg-[#eb5e28] hover:text-white transition-colors duration-200 cursor-pointer group text-[18px]'
            data-testid={`response-row-${response.applicantId}`}
          >
            {/* Кандидат */}
            <div style={{width: '350px'}} className='text-center truncate flex gap-[10px] items-center'>
              <Avatar className='w-[40px] h-[40px] cursor-pointer'>
                <AvatarImage alt='user' />
                <AvatarFallback>u</AvatarFallback>
              </Avatar>
              <span data-testid={`similarity-icon-${response.applicantId}`}>
                {response.name?.charAt(0).toUpperCase() + response.name?.slice(1).toLowerCase()}
              </span>
            </div>

            {/* Оценка резюме */}
            <div style={{width: '180px'}} className='text-center truncate'>
              {response.score?.toFixed(2)}/100
            </div>

            {/* Статус */}
            <div style={{width: '180px'}} className='text-center truncate'>
              <div className='group-hover:hidden'>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(response.status)}`}>
                  {getStatusText(response.status)}
                </span>
              </div>
              <div className='hidden group-hover:flex items-center gap-[10px]'>
                Перейти <img src={arrowIcon} alt='Перейти' className='w-[30px] h-[30px]'></img>
              </div>
            </div>

            {/* Проверен */}
            <div style={{width: '120px'}} className='text-center truncate'>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  response.checked ? 'text-green-600 bg-green-100' : 'text-gray-600 bg-gray-100'
                }`}
              >
                {response.checked ? 'Да' : 'Нет'}
              </span>
            </div>

            {/* Схожесть резюме */}
            <div 
              style={{width: '100px'}} 
              className='text-center truncate flex justify-center items-center relative'
              data-testid={`similarity-container-${response.applicantId}`}
            >
              {response.hasSimilarResume ? (
                <div 
                  className='flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 group-hover:bg-orange-200 transition-colors relative cursor-help'
                  onMouseEnter={() => setHoveredSimilarId(response.applicantId)}
                  onMouseLeave={() => setHoveredSimilarId(null)}
                >
                  <svg 
                    className='w-5 h-5 text-orange-600' 
                    fill='currentColor' 
                    viewBox='0 0 20 20'
                  >
                    <path 
                      fillRule='evenodd' 
                      d='M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z' 
                      clipRule='evenodd' 
                    />
                  </svg>
                  
                  {/* Tooltip */}
                  {hoveredSimilarId === response.applicantId && (
                    <div className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-sm rounded-lg shadow-lg whitespace-nowrap z-10'>
                      <div className='text-center'>
                        <div className='font-semibold text-orange-300'>⚠ Подозрение на дублирование</div>
                        <div className='mt-1'>Резюме похоже на резюме</div>
                        <div className='text-orange-300'>кандидата ID: {response.similarResumeApplicantId}</div>
                        <div className='mt-1 text-xs text-gray-300'>Требует дополнительной проверки</div>
                      </div>
                      {/* Стрелка tooltip */}
                      <div className='absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800'></div>
                    </div>
                  )}
                </div>
              ) : (
                <span className='text-gray-400'>—</span>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default ResponsesTable;
