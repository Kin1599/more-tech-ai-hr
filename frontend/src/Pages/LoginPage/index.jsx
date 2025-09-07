import React, {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Label} from '../../components/ui/label';
import {useStore} from '../../App/Store';
import logo from '../../Shared/imgs/logo.svg';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const {login} = useStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);

      if (result.success) {
        // Успешная авторизация - проверяем сохраненный URL
        const savedUrl = localStorage.getItem('redirectAfterLogin');
        if (savedUrl) {
          // Перенаправляем на сохраненный URL
          navigate(savedUrl);
        } else {
          // Перенаправляем на главную страницу
          navigate('/');
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      console.error('Ошибка при входе:', err);
      setError('Произошла ошибка при входе');
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
        <h1 className='text-2xl font-bold text-white text-center mb-8'>Вход в систему</h1>

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
              placeholder='Введите ваш пароль'
              className='w-full p-3 rounded-[10px] border-0 bg-[#F5F2EE] text-[#303030] focus:ring-2 focus:ring-white focus:bg-[#F5F2EE] hover:bg-[#F5F2EE]'
              required
            />
          </div>

          {/* Кнопка входа */}
          <Button
            type='submit'
            disabled={loading}
            className='w-full bg-white text-[#eb5e28] hover:bg-gray-100 hover:scale-105 font-semibold py-3 rounded-[10px] transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer'
          >
            {loading ? 'Вход...' : 'Войти'}
          </Button>
        </form>

        {/* Ссылка на регистрацию */}
        <div className='text-center mt-6'>
          <span className='text-white'>Нет аккаунта? </span>
          <Link
            to='/register'
            className='text-white underline hover:text-gray-200 transition-colors duration-200 font-medium'
          >
            Зарегистрироваться
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
