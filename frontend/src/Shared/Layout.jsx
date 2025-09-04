import React from 'react';
import {Outlet, useNavigate} from 'react-router-dom';
import styles from './Layout.module.css';
import {Avatar, AvatarImage, AvatarFallback} from '../components/ui/avatar';
import {useStore} from '../App/Store';
import logoIcon from './imgs/logo.svg';
// import userIcon from './imgs/user.svg';
import logoutIcon from './imgs/log-out.svg';

const Layout = () => {
  const navigate = useNavigate();
  const {logout} = useStore();

  const handleLogout = () => {
    if (window.confirm('Вы уверены, что хотите выйти?')) {
      logout();
      navigate('/login');
    }
  };

  return (
    <div className='bg-[#F5F2EE] flex flex-wrap flex-col'>
      <header className='flex items-center justify-between bg-[#eb5e28] p-[20px]'>
        <img src={logoIcon} alt='logo' className={styles.logo} />
        <div className='flex items-center gap-[20px]'>
          <Avatar className='w-[40px] h-[40px] cursor-pointer'>
            <AvatarImage alt='user' />
            <AvatarFallback>u</AvatarFallback>
          </Avatar>
          <span className='text-[#F5F2EE]'>User</span>
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
