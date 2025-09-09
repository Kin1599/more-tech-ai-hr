import React from 'react';
import {Button} from '../../../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../../components/ui/dropdown-menu';

const Dropdown = ({selectedFilter, onFilterChange}) => {
  const filterOptions = [
    {value: 'all', label: 'Все вакансии'},
    {value: 'active', label: 'Активные'},
    {value: 'closed', label: 'Закрытые'},
    {value: 'stopped', label: 'Остановленные'},
  ];

  const getCurrentLabel = () => {
    const option = filterOptions.find((opt) => opt.value === selectedFilter);
    return option ? option.label : 'Все вакансии';
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant='outline' className='w-[200px] h-[40px] bg-white border-gray-300 hover:bg-gray-50'>
          {getCurrentLabel()}
          <svg className='ml-2 h-4 w-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
          </svg>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className='w-[200px]'>
        {filterOptions.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onClick={() => onFilterChange(option.value)}
            className='cursor-pointer text-center'
          >
            {option.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default Dropdown;
