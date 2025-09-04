import React from 'react';
import {createRoot} from 'react-dom/client';
import Routing from './Routing';
import './index.css';
import {SearchProvider} from '../Shared/SearchContext';

const App = () => {
  return (
    <SearchProvider>
      <Routing />
    </SearchProvider>
  );
};

createRoot(document.getElementById('root')).render(<App />);
