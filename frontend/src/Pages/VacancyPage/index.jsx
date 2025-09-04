import React from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {useStore} from '../../App/Store';
import {Button} from '../../components/ui/button';
import StatusDropdown from './components/StatusDropdown';
import vtbLogo from '../../Shared/imgs/vtb.png';
import editIcon from '../../Shared/imgs/edit-3.svg';

const VacancyPage = () => {
  const {id} = useParams();
  const navigate = useNavigate();
  const {vacancies, updateVacancy} = useStore();

  // Находим вакансию по ID
  const vacancy = vacancies.find((v) => v.vacancyId === parseInt(id));

  // Функция для изменения статуса вакансии
  const handleStatusChange = (newStatus) => {
    updateVacancy(vacancy.vacancyId, {status: newStatus});
  };

  if (!vacancy) {
    return (
      <div className='flex flex-col items-center justify-center min-h-[400px]'>
        <h1 className='text-2xl font-semibold mb-4'>Вакансия не найдена</h1>
        <Button onClick={() => navigate('/')}>Вернуться к списку вакансий</Button>
      </div>
    );
  }

  return (
    <div className='flex flex-col gap-[20px]'>
      <div className='flex justify-between items-center'>
        <div className='text-[30px] font-semibold'>{vacancy.name}</div>
        <div className='flex gap-[20px]'>
          <Button className='bg-[#303030] hover:bg-[#eb5e28] hover:scale-105 transition-all duration-200 cursor-pointer flex items-center gap-[10px] p-[10px] pr-[16px] pl-[16px] text-[16px] text-white hover:text-white'>
            <img src={editIcon} alt='Редактировать' />
            Редактировать
          </Button>
          <StatusDropdown currentStatus={vacancy.status} onStatusChange={handleStatusChange} />
        </div>
      </div>
      <div className='flex justify-between'>
        <div className='flex flex-col gap-[10px]'>
          <div className='text-[20px]'>
            <span className='font-semibold'>Опыт работы:</span>
            {` от ${vacancy.age} лет`}
          </div>
          <div className='text-[20px]'>
            <span className='font-semibold'>Заработная плата:</span>
            {` ${vacancy.salary} рублей до уплаты налогов`}
          </div>
          <div className='text-[20px]'>
            <span className='font-semibold'>Локация:</span>
            {` ${vacancy.location}`}
          </div>
          <div className='text-[20px]'>
            <span className='font-semibold'>Формат:</span>
            {` ${vacancy.format}`}
          </div>
          <div className='text-[24px] font-semibold'>Описание вакансии:</div>
        </div>
        <div className='flex flex-col gap-[10px] items-center w-[200px]'>
          <img src={vtbLogo} alt='ВТБ' className='w-[100px] h-[100px] object-contain'></img>
          <div className='text-[24px] font-semibold'>Банк ВТБ</div>
        </div>
      </div>
    </div>
  );
};

export default VacancyPage;
