import React, {useState} from 'react';
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
import saveIcon from '../../Shared/imgs/edit-3.svg';
import arrowIcon from '../../Shared/imgs/arrow-right.svg';

const VacancyPage = () => {
  const {id} = useParams();
  const navigate = useNavigate();
  const {vacancies, updateVacancy, addVacancy, responses} = useStore();

  // Проверяем, создаем ли новую вакансию
  const isNewVacancy = !id;

  // Находим вакансию по ID или создаем пустую для новой вакансии
  const vacancy = isNewVacancy ? null : vacancies.find((v) => v.vacancyId === parseInt(id));

  // Получаем отклики для данной вакансии
  const vacancyResponses = vacancy ? responses[vacancy.vacancyId] || [] : [];

  // Состояние редактирования - для новой вакансии сразу в режиме редактирования
  const [isEditing, setIsEditing] = useState(isNewVacancy);
  const [editedVacancy, setEditedVacancy] = useState({
    name: vacancy?.name || '',
    age: vacancy?.age || '',
    salary: vacancy?.salary || '',
    salaryType: vacancy?.salaryType || 'до',
    location: vacancy?.location || '',
    format: vacancy?.format || 'Офис',
    status: vacancy?.status || 'active',
    description: vacancy?.description || '',
    prompt: vacancy?.prompt || '',
  });

  // Функция для изменения статуса вакансии
  const handleStatusChange = (newStatus) => {
    updateVacancy(vacancy.vacancyId, {status: newStatus});
  };

  // Функция для начала редактирования
  const handleEdit = () => {
    setIsEditing(true);
  };

  // Функция для сохранения изменений
  const handleSave = () => {
    if (isNewVacancy) {
      // Создаем новую вакансию
      const newVacancy = {
        ...editedVacancy,
        department: 'Отдел разработки', // По умолчанию
        responses: 0,
        responsesWithout: 0,
        date: new Date().toISOString().split('T')[0],
      };
      addVacancy(newVacancy);
      navigate('/');
    } else {
      // Обновляем существующую вакансию
      updateVacancy(vacancy.vacancyId, editedVacancy);
      setIsEditing(false);
    }
  };

  // Функция для отмены редактирования
  const handleCancel = () => {
    if (isNewVacancy) {
      // Для новой вакансии - возвращаемся на главную страницу
      navigate('/');
    } else {
      // Для существующей вакансии - сбрасываем изменения
      setEditedVacancy({
        name: vacancy?.name || '',
        age: vacancy?.age || '',
        salary: vacancy?.salary || '',
        salaryType: vacancy?.salaryType || 'до',
        location: vacancy?.location || '',
        format: vacancy?.format || 'Офис',
        status: vacancy?.status || 'active',
        description: vacancy?.description || '',
        prompt: vacancy?.prompt || '',
      });
      setIsEditing(false);
    }
  };

  // Функция для обновления полей редактирования
  const handleFieldChange = (field, value) => {
    setEditedVacancy((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  if (!vacancy && !isNewVacancy) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <h1 className='text-2xl font-semibold mb-4'>Вакансия не найдена</h1>
        <Button onClick={() => navigate('/')}>Вернуться к списку вакансий</Button>
      </div>
    );
  }

  return (
    <div className='flex flex-col gap-[10px]'>
      <div className='flex justify-between items-center mb-[10px]'>
        {isEditing ? (
          <Input
            value={editedVacancy.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            className='text-[30px] font-semibold bg-white border-2 border-gray-400 rounded-[10px] p-3 w-auto min-w-[400px] h-[45px]'
            placeholder='Название вакансии'
          />
        ) : (
          <div className='text-[30px] font-semibold'>{isNewVacancy ? 'Новая вакансия' : vacancy.name}</div>
        )}
        <div className='flex gap-[20px]'>
          {isEditing ? (
            <>
              <Button
                onClick={handleSave}
                className='bg-[#303030] hover:bg-[#eb5e28] hover:scale-105 transition-all duration-200 cursor-pointer flex items-center gap-[10px] p-[10px] pr-[16px] pl-[16px] text-[16px] text-white hover:text-white'
              >
                <img src={saveIcon} alt='Сохранить' />
                Опубликовать
              </Button>
              <Button
                onClick={handleCancel}
                className='bg-gray-500 hover:bg-gray-600 hover:scale-105 transition-all duration-200 cursor-pointer flex items-center gap-[10px] p-[10px] pr-[16px] pl-[16px] text-[16px] text-white hover:text-white'
              >
                Отмена
              </Button>
              <StatusDropdown
                currentStatus={editedVacancy.status}
                onStatusChange={(status) => handleFieldChange('status', status)}
              />
            </>
          ) : (
            <>
              <Button
                onClick={handleEdit}
                className='bg-[#303030] hover:bg-[#eb5e28] hover:scale-105 transition-all duration-200 cursor-pointer flex items-center gap-[10px] p-[10px] pr-[16px] pl-[16px] text-[16px] text-white hover:text-white'
              >
                <img src={editIcon} alt='Редактировать' />
                Редактировать
              </Button>
              <StatusDropdown currentStatus={vacancy.status} onStatusChange={handleStatusChange} />
            </>
          )}
        </div>
      </div>
      <div className='flex justify-between'>
        <div className='flex flex-col gap-[10px]'>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Опыт работы:</span>
            {isEditing ? (
              <Input
                value={editedVacancy.age}
                onChange={(e) => handleFieldChange('age', e.target.value)}
                className='w-[100px] bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px]'
                placeholder='0'
              />
            ) : (
              <span>{` от ${vacancy?.age || 0} лет`}</span>
            )}
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Заработная плата:</span>
            {isEditing ? (
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
            ) : (
              <span>{` ${vacancy?.salary || 0} рублей ${(vacancy?.salaryType || 'до') === 'до' ? 'до' : 'после'} вычета налогов`}</span>
            )}
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Локация:</span>
            {isEditing ? (
              <Input
                value={editedVacancy.location}
                onChange={(e) => handleFieldChange('location', e.target.value)}
                className='w-[200px] bg-white border-2 border-gray-400 rounded-[5px] p-1 text-[18px]'
                placeholder='Москва'
              />
            ) : (
              <span>{` ${vacancy?.location || ''}`}</span>
            )}
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Формат:</span>
            {isEditing ? (
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
            ) : (
              <span>{` ${vacancy?.format || 'Офис'}`}</span>
            )}
          </div>
          <div className='text-[24px] font-semibold'>Описание вакансии:</div>
        </div>
        <div className='flex flex-col gap-[10px] items-center w-[200px]'>
          <img src={vtbLogo} alt='ВТБ' className='w-[100px] h-[100px] object-contain'></img>
          <div className='text-[24px] font-semibold'>Банк ВТБ</div>
        </div>
      </div>
      {isEditing ? (
        <Textarea
          value={editedVacancy.description}
          onChange={(e) => handleFieldChange('description', e.target.value)}
          className='text-[20px] rounded-[20px] p-[20px] bg-white border-2 border-gray-400 min-h-[200px] resize-y'
          placeholder='Введите описание вакансии...'
        />
      ) : (
        <div className='text-[20px] rounded-[20px] p-[20px] bg-white'>{vacancy?.description || ''}</div>
      )}
      <div className='text-[24px] font-semibold'>Промпт:</div>
      {isEditing ? (
        <Textarea
          value={editedVacancy.prompt}
          onChange={(e) => handleFieldChange('prompt', e.target.value)}
          className='text-[20px] rounded-[20px] p-[20px] bg-white border-2 border-gray-400 min-h-[200px] resize-y'
          placeholder='Введите промпт для ИИ...'
        />
      ) : (
        <div className='text-[20px] rounded-[20px] p-[20px] bg-white'>{vacancy?.prompt || ''}</div>
      )}
      {!isEditing && (
        <>
          <div className='text-[24px] font-semibold'>Отклики:</div>
          <ResponsesTable responses={vacancyResponses} />
        </>
      )}
    </div>
  );
};

export default VacancyPage;
