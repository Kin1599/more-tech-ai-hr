import React, {useState, useEffect} from 'react';
import {Button} from '../../components/ui/button';
import CustomTable from '../../Shared/features/table';
import {Input} from '../../components/ui/input';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '../../components/ui/pagination';
import {useStore} from '../../App/Store';
import {useSearch} from '../../Shared/SearchContext';

const namesArr = [
  {name: 'Должность', width: '250px'},
  {name: 'Отдел', width: '400px'},
  {name: 'Откликов', width: '210px'},
  {name: 'Не просмотрено', width: '210px'},
  {name: 'Статус', width: '130px'},
];

const HomePage = () => {
  const {vacancies} = useStore();
  const {searchQuery} = useSearch();
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  // Фильтруем вакансии по поисковому запросу
  const filteredVacancies =
    searchQuery.trim() === ''
      ? vacancies
      : vacancies.filter((vacancy) => {
          if (!vacancy || !vacancy.name) {
            console.warn('Invalid vacancy data:', vacancy);
            return false;
          }
          return vacancy.name.toLowerCase().includes(searchQuery.toLowerCase());
        });

  const totalPages = Math.max(1, Math.ceil(filteredVacancies.length / itemsPerPage));

  // Сбрасываем страницу при изменении данных или поискового запроса
  useEffect(() => {
    setCurrentPage(1);
  }, [filteredVacancies.length, searchQuery]);

  // Проверяем, что текущая страница не превышает общее количество страниц
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const startIndex = Math.min((currentPage - 1) * itemsPerPage, filteredVacancies.length);
  const endIndex = Math.min(startIndex + itemsPerPage, filteredVacancies.length);
  const currentVacancies = filteredVacancies.slice(startIndex, endIndex);

  // Преобразуем данные для таблицы
  const tableData =
    currentVacancies.length > 0
      ? currentVacancies
          .map((vacancy) => {
            if (!vacancy) {
              console.warn('Empty vacancy in currentVacancies');
              return [];
            }

            return [
              {name: vacancy.name || 'Н/Д', width: '250px'},
              {name: vacancy.department || 'Н/Д', width: '400px'},
              {name: (vacancy.responses || 0).toString(), width: '210px'},
              {name: (vacancy.responsesWithout || 0).toString(), width: '210px'},
              {name: getStatusText(vacancy.status), width: '130px'},
            ];
          })
          .filter((row) => row.length > 0)
      : []; // Убираем пустые строки

  // Функция для отображения статуса
  function getStatusText(status) {
    switch (status) {
      case 'active':
        return 'Активная';
      case 'hold':
        return 'На паузе';
      case 'found':
        return 'Найдена';
      case 'approve':
        return 'Одобрена';
      default:
        return 'Неизвестно';
    }
  }

  // Генерируем массив страниц для отображения
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <div className='flex flex-col gap-[20px]'>
      {filteredVacancies.length === 0 && searchQuery.trim() !== '' ? (
        <div className='text-center py-8 text-gray-500'>По запросу "{searchQuery}" ничего не найдено</div>
      ) : (
        <CustomTable
          key={`${currentPage}-${searchQuery}-${filteredVacancies.length}`}
          data={tableData}
          namesArr={namesArr}
        />
      )}
      <Button className='flex gap-[10px] p-[16px] pb-[10px] pt-[10px] w-[209px] h-[40px] cursor-pointer mx-auto'>
        <img src='/src/shared/imgs/plus.svg'></img>
        Создать вакансию
      </Button>

      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
            />
          </PaginationItem>

          {getPageNumbers().map((page, index) => (
            <PaginationItem key={index}>
              {page === '...' ? (
                <span className='px-3 py-2'>...</span>
              ) : (
                <PaginationLink
                  onClick={() => setCurrentPage(page)}
                  isActive={currentPage === page}
                  className='cursor-pointer'
                >
                  {page}
                </PaginationLink>
              )}
            </PaginationItem>
          ))}

          <PaginationItem>
            <PaginationNext
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
              className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
};

export default HomePage;
