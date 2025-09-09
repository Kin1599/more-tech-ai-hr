import { useState, useCallback } from 'react'

let toastCount = 0

export const useToast = () => {
  const [toasts, setToasts] = useState([])

  const toast = useCallback(({ title, description, variant = 'default', duration = 5000 }) => {
    const id = toastCount++
    
    const newToast = {
      id,
      title,
      description,
      variant,
      duration
    }

    setToasts(prev => [...prev, newToast])

    // Автоматически удаляем уведомление через указанное время
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(toast => toast.id !== id))
      }, duration)
    }

    return id
  }, [])

  const dismiss = useCallback((toastId) => {
    setToasts(prev => prev.filter(toast => toast.id !== toastId))
  }, [])

  const success = useCallback((title, description, duration) => {
    return toast({ title, description, variant: 'success', duration })
  }, [toast])

  const error = useCallback((title, description, duration) => {
    return toast({ title, description, variant: 'destructive', duration })
  }, [toast])

  return {
    toasts,
    toast,
    success,
    error,
    dismiss
  }
}
