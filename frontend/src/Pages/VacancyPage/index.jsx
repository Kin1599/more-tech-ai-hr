import React, {useState, useRef} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {useStore} from '../../App/Store';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Textarea} from '../../components/ui/textarea';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import StatusDropdown from './components/StatusDropdown';
import ResponsesTable from './components/ResponsesTable';
import vtbLogo from '../../Shared/imgs/vtb.png';
import editIcon from '../../Shared/imgs/edit-3.svg';

const VacancyPage = () => {
  const {id} = useParams();
  const navigate = useNavigate();
  const {vacancies, updateVacancy, responses} = useStore();
  const fileInputRef = useRef(null);

  // Проверяем, создаем ли новую вакансию
  const isNewVacancy = !id;

  // Находим вакансию по ID или создаем пустую для новой вакансии
  const vacancy = isNewVacancy ? null : vacancies.find((v) => v.vacancyId === parseInt(id));

  // Получаем отклики для данной вакансии
  const vacancyResponses = vacancy ? responses[vacancy.vacancyId] || [] : [];

  // Состояние редактирования - для новой вакансии сразу в режиме редактирования
  const [isEditing] = useState(isNewVacancy);

  // Функция для загрузки файла
  const handleFileUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Функция для обработки выбранного файла
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      console.log('Выбран файл:', file.name);
      // Здесь можно добавить логику обработки файла
      alert(`Файл "${file.name}" успешно загружен!`);
    }
  };

  // Функция для изменения статуса вакансии
  const handleStatusChange = (newStatus) => {
    updateVacancy(vacancy.vacancyId, {status: newStatus});
  };

  // Функция для начала редактирования - теперь загружает файл
  const handleEdit = () => {
    handleFileUpload();
  };

  if (!vacancy && !isNewVacancy) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <h1 className='text-2xl font-semibold mb-4'>Вакансия не найдена</h1>
        <Button onClick={() => navigate('/hr')}>Вернуться к списку вакансий</Button>
      </div>
    );
  }

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

      {/* Кнопка назад */}
      <div className='mb-4'>
        <Button onClick={() => navigate('/hr')} variant='outline' className='flex items-center gap-2 cursor-pointer'>
          <svg className='w-4 h-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M15 19l-7-7 7-7' />
          </svg>
          Назад к списку вакансий
        </Button>
      </div>

      <div className='flex justify-between items-center mb-[10px]'>
        {/* Закомментированная форма редактирования названия */}
        {/* {isEditing ? (
          <Input
            value={editedVacancy.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            className='text-[30px] font-semibold bg-white border-2 border-gray-400 rounded-[10px] p-3 w-auto min-w-[400px] h-[45px]'
            placeholder='Название вакансии'
          />
        ) : ( */}
        <div className='text-[30px] font-semibold'>{isNewVacancy ? 'Новая вакансия' : vacancy?.name || 'Вакансия'}</div>
        {/* )} */}
        <div className='flex gap-[20px]'>
          <Button
            onClick={handleEdit}
            className='bg-[#303030] hover:bg-[#eb5e28] hover:scale-105 transition-all duration-200 cursor-pointer flex items-center gap-[10px] p-[10px] pr-[16px] pl-[16px] text-[16px] text-white hover:text-white'
          >
            <img src={editIcon} alt='Загрузить файл' />
            Редактировать вакансию
          </Button>
          {!isNewVacancy && vacancy && (
            <StatusDropdown currentStatus={vacancy.status} onStatusChange={handleStatusChange} />
          )}
        </div>
      </div>
      <div className='flex justify-between'>
        <div className='flex flex-col gap-[10px]'>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Опыт работы:</span>
            {/* Закомментированная форма редактирования опыта */}
            {/* {isEditing ? (
              <Input
                value={editedVacancy.age}
                onChange={(e) => handleFieldChange('age', e.target.value)}
                className='w-[100px] bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px]'
                placeholder='0'
              />
            ) : ( */}
            <span>{` от ${vacancy?.age || 0} лет`}</span>
            {/* )} */}
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Заработная плата:</span>
            {/* Закомментированная форма редактирования зарплаты */}
            {/* {isEditing ? (
              <div className='flex items-center gap-2'>
                <Input
                  value={editedVacancy.salary}
                  onChange={(e) => handleFieldChange('salary', e.target.value)}
                  className='w-[150px] bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px]'
                  placeholder='100000'
                />
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant='outline'
                      className='bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px] h-auto min-w-[180px] justify-between'
                    >
                      <span>{editedVacancy.salaryType === 'до' ? 'до вычета налогов' : 'после вычета налогов'}</span>
                      <img src={arrowIcon} alt='' className='w-4 h-4 rotate-90' />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem onClick={() => handleFieldChange('salaryType', 'до')}>
                      до вычета налогов
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleFieldChange('salaryType', 'после')}>
                      после вычета налогов
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ) : ( */}
            <span>{` ${vacancy?.salary || 0} рублей ${(vacancy?.salaryType || 'до') === 'до' ? 'до' : 'после'} вычета налогов`}</span>
            {/* )} */}
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Локация:</span>
            {/* Закомментированная форма редактирования локации */}
            {/* {isEditing ? (
              <Input
                value={editedVacancy.location}
                onChange={(e) => handleFieldChange('location', e.target.value)}
                className='w-[200px] bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px]'
                placeholder='Москва'
              />
            ) : ( */}
            <span>{` ${vacancy?.location || ''}`}</span>
            {/* )} */}
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Формат:</span>
            {/* Закомментированная форма редактирования формата */}
            {/* {isEditing ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant='outline'
                    className='bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px] h-auto min-w-[120px] justify-start'
                  >
                    {editedVacancy.format}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => handleFieldChange('format', 'Офис')}>Офис</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleFieldChange('format', 'Удаленка')}>Удаленка</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleFieldChange('format', 'Гибрид')}>Гибрид</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : ( */}
            <span>{` ${vacancy?.format || 'Офис'}`}</span>
            {/* )} */}
          </div>
          <div className='text-[24px] font-semibold'>Описание вакансии:</div>
        </div>
        <div className='flex flex-col gap-[10px] items-center w-[200px]'>
          <img src={vtbLogo} alt='ВТБ' className='w-[100px] h-[100px] object-contain'></img>
          <div className='text-[24px] font-semibold'>Банк ВТБ</div>
        </div>
      </div>
      {/* Закомментированная форма редактирования описания */}
      {/* {isEditing ? (
        <Textarea
          value={editedVacancy.description}
          onChange={(e) => handleFieldChange('description', e.target.value)}
          className='text-[20px] rounded-[20px] p-[20px] bg-white border-2 border-gray-400 min-h-[200px] resize-y'
          placeholder='Введите описание вакансии...'
        />
      ) : ( */}
      <div className='text-[20px] rounded-[20px] p-[20px] bg-white'>{vacancy?.description || ''}</div>
      {/* )} */}
      <div className='text-[24px] font-semibold'>Промпт:</div>
      {/* Закомментированная форма редактирования промпта */}
      {/* {isEditing ? (
        <Textarea
          value={editedVacancy.prompt}
          onChange={(e) => handleFieldChange('prompt', e.target.value)}
          className='text-[20px] rounded-[20px] p-[20px] bg-white border-2 border-gray-400 min-h-[200px] resize-y'
          placeholder='Введите промпт для ИИ...'
        />
      ) : ( */}
      <div className='text-[20px] rounded-[20px] p-[20px] bg-white'>{vacancy?.prompt || ''}</div>
      {/* )} */}
      {!isEditing && (
        <>
          <div className='text-[24px] font-semibold'>Отклики:</div>
          <ResponsesTable responses={vacancyResponses} vacancyId={vacancy?.vacancyId || id} />
        </>
      )}
    </div>
  );
};

export default VacancyPage;
