import {clsx} from 'clsx';
import {twMerge} from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Функция для капитализации первой буквы строки
export function capitalizeFirst(str) {
  if (!str || typeof str !== 'string') return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}
