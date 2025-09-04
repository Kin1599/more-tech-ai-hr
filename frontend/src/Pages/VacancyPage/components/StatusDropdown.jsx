import React, {useState} from 'react';
import {Button} from '../../../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../../components/ui/dropdown-menu';

const StatusDropdown = ({currentStatus, onStatusChange}) => {
  const [isOpen, setIsOpen] = useState(false);

  const statusOptions = [
    {value: 'active', label: 'Активная'},
    {value: 'hold', label: 'На паузе'},
    {value: 'found', label: 'Найдена'},
    {value: 'approve', label: 'Одобрена'},
  ];

  const getCurrentLabel = () => {
    const option = statusOptions.find((opt) => opt.value === currentStatus);
    return option ? option.label : 'Неизвестно';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'hold':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'found':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'approve':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <DropdownMenu onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant='outline'
          className={`w-[204px] h-[40px] border ${getStatusColor(currentStatus)} hover:opacity-80`}
        >
          {getCurrentLabel()}
          <svg
            className={`ml-2 h-4 w-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : 'rotate-0'}`}
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
          </svg>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className='w-[180px]'>
        {statusOptions.map((option) => (
          <DropdownMenuItem key={option.value} onClick={() => onStatusChange(option.value)} className='cursor-pointer'>
            {option.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default StatusDropdown;
