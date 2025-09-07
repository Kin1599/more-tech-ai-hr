import React, {useState, useEffect, useRef} from 'react';
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
import Dropdown from './components/Dropdown';
import plusIcon from '../../Shared/imgs/plus.svg';

const namesArr = [
  {name: 'Должность', width: '250px'},
  {name: 'Регион', width: '400px'},
  {name: 'Откликов', width: '210px'},
  {name: 'Зарплата', width: '210px'},
  {name: 'Статус', width: '130px'},
];

const HomePage = () => {
  const {vacancies, fetchVacancies, uploadCV} = useStore();
  const fileInputRef = useRef(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  // Загружаем вакансии при монтировании компонента
  useEffect(() => {
    fetchVacancies();
  }, [fetchVacancies]);

  // Функция для загрузки файла
  const handleFileUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Функция для обработки выбранного файла
  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (file) {
      console.log('Выбран файл:', file.name);

      try {
        console.log(file);
        const result = await uploadCV(file);

        if (result.success) {
          alert(`Файл "${file.name}" успешно загружен! Вакансия создана.`);
          // Обновляем список вакансий
          await fetchVacancies();
        } else {
          alert(`Ошибка при загрузке файла: ${result.error}`);
        }
      } catch (error) {
        console.error('Ошибка при загрузке файла:', error);
        alert('Произошла ошибка при загрузке файла');
      }

      // Очищаем input
      event.target.value = '';
    }
  };

  // Фильтруем вакансии по поисковому запросу и статусу
  const filteredVacancies = vacancies.filter((vacancy) => {
    if (!vacancy || !vacancy.name) {
      console.warn('Invalid vacancy data:', vacancy);
      return false;
    }

    // Фильтр по поисковому запросу
    const matchesSearch = searchQuery.trim() === '' || vacancy.name.toLowerCase().includes(searchQuery.toLowerCase());

    // Фильтр по статусу
    let matchesStatus = true;
    if (statusFilter === 'active') {
      matchesStatus = vacancy.status === 'active';
    } else if (statusFilter === 'closed') {
      matchesStatus = ['closed', 'stopped'].includes(vacancy.status);
    }
    // Если statusFilter === 'all', то matchesStatus остается true

    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.max(1, Math.ceil(filteredVacancies.length / itemsPerPage));

  // Сбрасываем страницу при изменении данных, поискового запроса или фильтра статуса
  useEffect(() => {
    setCurrentPage(1);
  }, [filteredVacancies.length, searchQuery, statusFilter]);

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
              return null;
            }

            const row = [
              {name: vacancy.name || 'Н/Д', width: '250px'},
              {name: vacancy.region || 'Н/Д', width: '400px'},
              {name: (vacancy.responces || 0).toString(), width: '210px'},
              {name: `${vacancy.salaryMin || 0} - ${vacancy.salaryMax || 0}`, width: '210px'},
              {name: getStatusText(vacancy.status), width: '130px'},
            ];

            // Добавляем vacancyId к строке
            row.vacancyId = vacancy.vacancyId;
            return row;
          })
          .filter((row) => row !== null)
      : []; // Убираем пустые строки

  // Функция для отображения статуса
  function getStatusText(status) {
    switch (status) {
      case 'active':
        return 'Активная';
      case 'closed':
        return 'Закрыта';
      case 'stopped':
        return 'Остановлена';
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
  console.log(vacancies);
  return (
    <div className='flex flex-col gap-[10px]'>
      {/* Скрытый input для загрузки файла */}
      <input
        type='file'
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{display: 'none'}}
        accept='.pdf,.doc,.docx,.txt'
      />

      <div className='flex justify-between items-center mb-10'>
        <div className='text-[30px] font-semibold'>Вакансии</div>
        <Input
          className='bg-white w-[500px] h-[40px] rounded-[10px] p-[10px]'
          placeholder='Поиск по должности'
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <Button
          onClick={handleFileUpload}
          className='flex gap-[10px] p-[16px] pb-[10px] pt-[10px] w-[209px] h-[40px] cursor-pointer'
        >
          <img src={plusIcon} alt='Загрузить файл' />
          Загрузить вакансию
        </Button>
        <Dropdown selectedFilter={statusFilter} onFilterChange={setStatusFilter} />
      </div>
      {filteredVacancies.length === 0 ? (
        <div className='text-center py-8 text-gray-500'>
          {searchQuery.trim() !== '' || statusFilter !== 'all'
            ? 'По заданным критериям ничего не найдено'
            : 'Вакансии не найдены'}
        </div>
      ) : (
        <CustomTable
          key={`${currentPage}-${searchQuery}-${statusFilter}-${filteredVacancies.length}`}
          data={tableData}
          namesArr={namesArr}
        />
      )}

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
