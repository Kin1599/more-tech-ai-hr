import React from 'react';
import {createRoot} from 'react-dom/client';
import Routing from './Routing';
import './index.css';
import {SearchProvider} from '../Shared/SearchContext';
import ToastContainer from '../components/ui/ToastContainer';
import {useStore} from './store';

const App = () => {
  const {toasts, removeToast} = useStore();

  return (
    <SearchProvider>
      <Routing />
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </SearchProvider>
  );
};

createRoot(document.getElementById('root')).render(<App />);
