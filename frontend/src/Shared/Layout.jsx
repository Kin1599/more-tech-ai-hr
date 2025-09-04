import React from 'react';
import {Outlet, useLocation, useNavigate} from 'react-router-dom';
import styles from './Layout.module.css';
import {Input} from '../components/ui/input';
import {Avatar, AvatarImage, AvatarFallback} from '../components/ui/avatar';
import {useSearch} from './SearchContext';
import {useStore} from '../App/Store';

const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isHomePage = location.pathname === '/';
  const {searchQuery, setSearchQuery} = useSearch();
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
        <img src='src/shared/imgs/logo.svg' alt='logo' className={styles.logo} />
        <div className='flex items-center gap-[20px]'>
          {isHomePage && (
            <Input
              className='bg-white w-[384px] h-[40px] rounded-[10px] p-[10px]'
              placeholder='Поиск по должности'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          )}
          <Avatar className='w-[40px] h-[40px] cursor-pointer'>
            <AvatarImage src='src/shared/imgs/user.svg' alt='user' />
            <AvatarFallback>u</AvatarFallback>
          </Avatar>
          <span className='text-[#F5F2EE]'>User</span>
          <img
            src='src/shared/imgs/log-out.svg'
            alt='log'
            className='w-[35px] h-[35px] cursor-pointer'
            onClick={handleLogout}
          />
        </div>
      </header>
      <div className='p-[20px] pb-[52px] bg-[#F5F2EE] h-full'>
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;
