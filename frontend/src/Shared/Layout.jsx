import React, {useEffect} from 'react';
import {Outlet, useNavigate, useLocation} from 'react-router-dom';
import styles from './layout.module.css';
import {Avatar, AvatarImage, AvatarFallback} from '../components/ui/avatar';
import {useStore} from '../App/store';
import logoIcon from './imgs/logo.svg';
import logoutIcon from './imgs/log-out.svg';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {logout, user} = useStore();

  const handleLogout = () => {
    if (window.confirm('Вы уверены, что хотите выйти?')) {
      logout();
      navigate('/login');
    }
  };

  // Проверяем, находимся ли мы на страницах логина или регистрации
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  // Сохраняем URL для редиректа после логина, если пользователь не авторизован
  useEffect(() => {
    console.log('Layout useEffect - user:', user, 'isAuthPage:', isAuthPage, 'pathname:', location.pathname);

    if (!user && !isAuthPage) {
      // Сохраняем текущий URL для редиректа после логина
      const urlToSave = location.pathname + location.search;
      // Проверяем, что это страница кандидата
      if (urlToSave.startsWith('/applicant/')) {
        localStorage.setItem('redirectAfterLogin', urlToSave);
        console.log('Сохраняем URL для редиректа:', urlToSave);
        console.log('Проверяем localStorage:', localStorage.getItem('redirectAfterLogin'));
      }
    }
  }, [user, isAuthPage, location.pathname, location.search]);

  // Если это страница авторизации, показываем только контент без навигации
  if (isAuthPage) {
    return <Outlet />;
  }

  return (
    <div className='bg-[#F5F2EE] flex flex-wrap flex-col'>
      <header className='flex items-center justify-between bg-[#eb5e28] p-[20px]'>
        <img
          src={logoIcon}
          alt='logo'
          className={`${styles.logo} cursor-pointer hover:opacity-80 transition-opacity duration-200`}
          onClick={() => navigate('/')}
        />
        <div className='flex items-center gap-[20px]'>
          <Avatar className='w-[40px] h-[40px] cursor-pointer'>
            <AvatarImage alt='user' />
            <AvatarFallback>u</AvatarFallback>
          </Avatar>
          <span className='text-[#F5F2EE]'>{user?.name || 'User'}</span>
          <span className='text-[#F5F2EE] text-sm opacity-75'>({user?.role === 'hr' ? 'HR' : 'Кандидат'})</span>
          <img src={logoutIcon} alt='log' className='w-[35px] h-[35px] cursor-pointer' onClick={handleLogout} />
        </div>
      </header>
      <div className='p-[20px] pb-[52px] bg-[#F5F2EE] h-full'>
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;
