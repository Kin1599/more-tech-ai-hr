import React, {useState, useRef, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {useStore} from '../../App/Store';
import {Button} from '../../components/ui/button';
import StatusDropdown from './components/StatusDropdown';
import ResponsesTable from './components/ResponsesTable';
import vtbLogo from '../../Shared/imgs/vtb.png';
import editIcon from '../../Shared/imgs/edit-3.svg';

const VacancyPage = () => {
  const {id} = useParams();
  const navigate = useNavigate();
  const {vacancies, updateVacancy, uploadCV, fetchVacancy, changeVacancyStatus} = useStore();
  const fileInputRef = useRef(null);

  // Проверяем, создаем ли новую вакансию
  const isNewVacancy = !id;

  // Состояние для загруженной вакансии
  const [vacancy, setVacancy] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Получаем отклики из данных вакансии
  const vacancyResponses = vacancy?.detailResponces || [];

  // Состояние редактирования - для новой вакансии сразу в режиме редактирования
  const [isEditing] = useState(isNewVacancy);

  // Состояние для дропдауна описания
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(true);

  // Загружаем вакансию при монтировании компонента
  useEffect(() => {
    if (id && !isNewVacancy) {
      const loadVacancy = async () => {
        setIsLoading(true);
        try {
          // Сначала ищем в store
          const existingVacancy = vacancies.find((v) => v.vacancyId === parseInt(id));
          if (existingVacancy) {
            setVacancy(existingVacancy);
          } else {
            // Если не найдена в store, загружаем с API
            const result = await fetchVacancy(parseInt(id));
            if (result.success) {
              setVacancy(result.data);
              // Обновляем вакансию в store
              updateVacancy(parseInt(id), result.data);
            }
          }
        } catch (error) {
          console.error('Ошибка при загрузке вакансии:', error);
        } finally {
          setIsLoading(false);
        }
      };
      loadVacancy();
    }
  }, [id, isNewVacancy, fetchVacancy, updateVacancy, vacancies]);

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
        const result = await uploadCV(file, vacancy?.vacancyId);

        if (result.success) {
          alert(`Файл "${file.name}" успешно загружен! Вакансия обновлена.`);
          // Обновляем данные вакансии
          if (vacancy?.vacancyId) {
            // Обновляем существующую вакансию
            updateVacancy(vacancy.vacancyId, result.data);
          }
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

  // Функция для изменения статуса вакансии
  const handleStatusChange = async (newStatus) => {
    if (!vacancy?.vacancyId) return;

    try {
      const result = await changeVacancyStatus(vacancy.vacancyId, newStatus);

      if (result.success) {
        // Статус уже обновлен в store через changeVacancyStatus
        console.log('Статус вакансии успешно изменен');
      } else {
        alert(`Ошибка при изменении статуса: ${result.error}`);
      }
    } catch (error) {
      console.error('Ошибка при изменении статуса:', error);
      alert('Произошла ошибка при изменении статуса');
    }
  };

  // Функция для начала редактирования - теперь загружает файл
  const handleEdit = () => {
    handleFileUpload();
  };

  if (isLoading) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <div className='text-2xl font-semibold mb-4'>Загрузка вакансии...</div>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28]'></div>
      </div>
    );
  }

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
            <span>{` от ${vacancy?.exp || 0} лет`}</span>
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Заработная плата:</span>
            <span>{` ${vacancy?.salaryMin || 0} - ${vacancy?.salaryMax || 0} рублей`}</span>
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Локация:</span>
            <span>{` ${vacancy?.city || ''}, ${vacancy?.address || ''}`}</span>
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Тип занятости:</span>
            <span>{` ${vacancy?.busyType || ''}`}</span>
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>График:</span>
            <span>{` ${vacancy?.graph || ''}`}</span>
          </div>
          <div className='text-[20px] flex items-center gap-2'>
            <span className='font-semibold'>Откликов:</span>
            <span>{` ${vacancy?.responses || 0}`}</span>
          </div>
        </div>
        <div className='flex flex-col gap-[10px] items-center w-[200px]'>
          <img src={vtbLogo} alt='ВТБ' className='w-[100px] h-[100px] object-contain'></img>
          <div className='text-[24px] font-semibold'>Банк ВТБ</div>
        </div>
      </div>

      {/* Дропдаун с описанием вакансии */}
      {vacancy?.description && (
        <div>
          <div
            className='flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors duration-200 p-4 rounded-lg border border-gray-200'
            onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
          >
            <h3 className='text-[24px] font-semibold'>Описание вакансии</h3>
            <div
              className={`transform transition-transform duration-300 ease-in-out ${isDescriptionExpanded ? 'rotate-180' : 'rotate-0'}`}
            >
              <svg className='w-5 h-5 text-gray-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
              </svg>
            </div>
          </div>
          <div
            className={`overflow-hidden transition-all duration-300 ease-in-out ${
              isDescriptionExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
            }`}
          >
            <div className='mt-2 bg-white rounded-lg border border-gray-200 p-4'>
              <p className='text-gray-700 leading-relaxed'>{vacancy.description}</p>
            </div>
          </div>
        </div>
      )}
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
