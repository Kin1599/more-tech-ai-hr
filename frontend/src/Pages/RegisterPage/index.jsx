import React, {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Label} from '../../components/ui/label';
import {useStore} from '../../App/store';
import logo from '../../Shared/imgs/logo.svg';

const RegisterPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('applicant');
  const [resumeFile, setResumeFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const {register} = useStore();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Проверяем тип файла
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ];
      if (!allowedTypes.includes(file.type)) {
        setError('Пожалуйста, выберите файл в формате PDF или DOC/DOCX');
        return;
      }

      // Проверяем размер файла (максимум 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Размер файла не должен превышать 5MB');
        return;
      }

      setResumeFile(file);
      setError('');
    }
  };

  const handleRoleChange = (e) => {
    const newRole = e.target.value;
    setRole(newRole);
    // Очищаем файл резюме при смене роли на HR
    if (newRole === 'hr') {
      setResumeFile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (password.length < 3) {
      setError('Пароль должен содержать минимум 3 символа');
      return;
    }

    if (role === 'applicant' && !resumeFile) {
      setError('Пожалуйста, прикрепите резюме');
      return;
    }

    setLoading(true);

    try {
      console.log('Проверяем localStorage перед регистрацией:', localStorage.getItem('redirectAfterLogin'));
      const result = await register(email, password, resumeFile, role);
      console.log('Проверяем localStorage после регистрации:', localStorage.getItem('redirectAfterLogin'));

      if (result.success) {
        // Успешная регистрация - проверяем сохраненный URL
        const savedUrl = localStorage.getItem('redirectAfterLogin');
        console.log('Сохраненный URL:', savedUrl);
        console.log('Полный результат регистрации:', result);
        console.log('Роль пользователя из result.data:', result.data?.role);
        console.log('Роль пользователя из result.user:', result.user?.role);

        if (savedUrl) {
          console.log('Перенаправляем на сохраненный URL:', savedUrl);
          // Перенаправляем на сохраненный URL
          navigate(savedUrl);
          // Очищаем сохраненный URL ПОСЛЕ навигации
          setTimeout(() => {
            localStorage.removeItem('redirectAfterLogin');
          }, 100);
        } else {
          // Перенаправляем на главную страницу в зависимости от роли
          const userRole = result.data?.role || result.user?.role;
          if (userRole === 'hr') {
            console.log('Перенаправляем HR на /hr');
            navigate('/hr');
          } else if (userRole === 'applicant') {
            console.log('Перенаправляем кандидата на /applicant');
            navigate('/applicant');
          } else {
            console.log('Перенаправляем на главную страницу');
            navigate('/');
          }
        }
      } else {
        setError(result.error);
      }
    } catch (error) {
      console.error('Ошибка при регистрации:', error);
      setError('Произошла ошибка при регистрации');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='min-h-screen bg-gray-50 flex items-center justify-center p-4'>
      <div className='bg-[#eb5e28] rounded-[20px] p-8 w-full max-w-md shadow-lg'>
        {/* Логотип */}
        <div className='flex justify-center mb-8'>
          <img src={logo} alt='Логотип' className='h-16 w-auto' />
        </div>

        {/* Заголовок */}
        <h1 className='text-2xl font-bold text-white text-center mb-8'>Регистрация</h1>

        {/* Плашка о недоступности HR регистрации */}
        {role === 'hr' && (
          <div className='bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded-[10px] mb-4'>
            <div className='flex items-center'>
              <div className='flex-shrink-0'>
                <svg className='h-5 w-5 text-yellow-400' viewBox='0 0 20 20' fill='currentColor'>
                  <path
                    fillRule='evenodd'
                    d='M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z'
                    clipRule='evenodd'
                  />
                </svg>
              </div>
              <div className='ml-3'>
                <p className='text-sm font-medium'>Регистрация HR не будет доступна в продакшене</p>
              </div>
            </div>
          </div>
        )}

        {/* Сообщение об ошибке */}
        {error && (
          <div className='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-[10px] mb-4'>{error}</div>
        )}

        {/* Форма */}
        <form onSubmit={handleSubmit} className='space-y-6'>
          {/* Email */}
          <div className='space-y-2'>
            <Label htmlFor='email' className='text-white font-medium'>
              Email
            </Label>
            <Input
              id='email'
              type='email'
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder='Введите ваш email'
              className='w-full p-3 rounded-[10px] border-0 bg-[#F5F2EE] text-[#303030] focus:ring-2 focus:ring-white focus:bg-[#F5F2EE] hover:bg-[#F5F2EE]'
              required
            />
          </div>

          {/* Роль */}
          <div className='space-y-2'>
            <Label htmlFor='role' className='text-white font-medium'>
              Роль
            </Label>
            <select
              id='role'
              value={role}
              onChange={handleRoleChange}
              className='w-full p-3 rounded-[10px] border-0 bg-[#F5F2EE] text-[#303030] focus:ring-2 focus:ring-white focus:bg-[#F5F2EE] hover:bg-[#F5F2EE]'
              required
            >
              <option value='applicant'>Кандидат</option>
              <option value='hr'>HR</option>
            </select>
          </div>

          {/* Пароль */}
          <div className='space-y-2'>
            <Label htmlFor='password' className='text-white font-medium'>
              Пароль
            </Label>
            <Input
              id='password'
              type='password'
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder='Введите пароль'
              className='w-full p-3 rounded-[10px] border-0 bg-[#F5F2EE] text-[#303030] focus:ring-2 focus:ring-white focus:bg-[#F5F2EE] hover:bg-[#F5F2EE]'
              required
            />
          </div>

          {/* Подтверждение пароля */}
          <div className='space-y-2'>
            <Label htmlFor='confirmPassword' className='text-white font-medium'>
              Подтвердите пароль
            </Label>
            <Input
              id='confirmPassword'
              type='password'
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder='Подтвердите пароль'
              className='w-full p-3 rounded-[10px] border-0 bg-[#F5F2EE] text-[#303030] focus:ring-2 focus:ring-white focus:bg-[#F5F2EE] hover:bg-[#F5F2EE]'
              required
            />
          </div>

          {/* Загрузка резюме - только для кандидатов */}
          {role === 'applicant' && (
            <div className='space-y-2'>
              <Label htmlFor='resume' className='text-white font-medium'>
                Резюме (PDF, DOC, DOCX)
              </Label>
              <div className='relative'>
                <Input
                  id='resume'
                  type='file'
                  onChange={handleFileChange}
                  accept='.pdf,.doc,.docx'
                  className='w-full p-3 rounded-[10px] border-0 bg-[#F5F2EE] text-[#303030] focus:ring-2 focus:ring-white focus:bg-[#F5F2EE] hover:bg-[#F5F2EE] file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-white file:text-[#eb5e28] hover:file:bg-gray-100 h-[55px]'
                  required
                />
              </div>
            </div>
          )}

          {/* Кнопка регистрации */}
          <Button
            type='submit'
            disabled={loading}
            className='w-full bg-white text-[#eb5e28] hover:bg-gray-100 hover:scale-105 font-semibold py-3 rounded-[10px] transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed'
          >
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </Button>
        </form>

        {/* Ссылка на логин */}
        <div className='text-center mt-6'>
          <span className='text-white'>Уже есть аккаунт? </span>
          <Link
            to='/login'
            className='text-white underline hover:text-gray-200 transition-colors duration-200 font-medium'
          >
            Войти
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
