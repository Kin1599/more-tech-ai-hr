import React from 'react';
import {Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport} from './toast';
import {CheckCircle, XCircle, Info} from 'lucide-react';

const ToastContainer = ({toasts, onDismiss}) => {
  const getIcon = (variant) => {
    switch (variant) {
      case 'success':
        return <CheckCircle className='h-5 w-5 text-green-600' />;
      case 'destructive':
        return <XCircle className='h-5 w-5 text-red-600' />;
      default:
        return <Info className='h-5 w-5 text-blue-600' />;
    }
  };

  return (
    <ToastProvider>
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          variant={toast.variant}
          className={`mb-4 shadow-lg border-l-4 ${
            toast.variant === 'success'
              ? 'border-l-green-500 bg-green-50'
              : toast.variant === 'destructive'
                ? 'border-l-red-500 bg-red-50'
                : 'border-l-blue-500 bg-blue-50'
          }`}
        >
          <div className='flex items-start space-x-3'>
            {getIcon(toast.variant)}
            <div className='flex-1'>
              {toast.title && <ToastTitle className='text-sm font-semibold'>{toast.title}</ToastTitle>}
              {toast.description && (
                <ToastDescription className='text-sm text-gray-600 mt-1'>{toast.description}</ToastDescription>
              )}
            </div>
          </div>
          <ToastClose onClick={() => onDismiss(toast.id)} className='absolute right-2 top-2' />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  );
};

export default ToastContainer;
