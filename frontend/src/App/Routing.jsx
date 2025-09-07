import React from 'react';
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import Layout from '../Shared/Layout';
import HomePage from '../Pages/HomePage';
import AboutPage from '../Pages/AboutPage';
import LoginPage from '../Pages/LoginPage';
import RegisterPage from '../Pages/RegisterPage';
import VacancyPage from '../Pages/VacancyPage';
import VacancyApplicantPage from '../Pages/vacancyApplicantPage';
import ApplicantHomePage from '../Pages/ApplicantHomePage';
import ApplicantVacancyPage from '../Pages/ApplicantVacancyPage';
import NotFoundPage from '../Pages/NotFoundPage';

import {Navigate} from 'react-router-dom';
import {useStore} from '../App/Store';

const ProtectedRoute = ({children}) => {
  const {user} = useStore();

  if (!user) {
    return <Navigate to='/login' replace />;
  }

  return children;
};

const HRRoute = ({children}) => {
  const {user} = useStore();

  if (!user) {
    return <Navigate to='/login' replace />;
  }

  if (user.role !== 'hr') {
    return <Navigate to='/applicant' replace />;
  }

  return children;
};

const ApplicantRoute = ({children}) => {
  const {user} = useStore();

  if (!user) {
    return <Navigate to='/login' replace />;
  }

  if (user.role !== 'applicant') {
    return <Navigate to='/hr' replace />;
  }

  return children;
};

const RoleBasedRedirect = () => {
  const {user} = useStore();

  if (!user) {
    return <Navigate to='/login' replace />;
  }

  if (user.role === 'hr') {
    return <Navigate to='/hr' replace />;
  } else if (user.role === 'applicant') {
    return <Navigate to='/applicant' replace />;
  }

  return <Navigate to='/login' replace />;
};

const Routing = () => {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Layout />}>
          {/* Главная страница - перенаправляет на основе роли */}
          <Route index element={<RoleBasedRedirect />} />

          {/* HR маршруты */}
          <Route
            path='/hr'
            element={
              <HRRoute>
                <HomePage />
              </HRRoute>
            }
          />
          <Route
            path='/hr/about'
            element={
              <HRRoute>
                <AboutPage />
              </HRRoute>
            }
          />
          <Route
            path='/hr/createVacancy'
            element={
              <HRRoute>
                <VacancyPage />
              </HRRoute>
            }
          />
          <Route
            path='/hr/vacancy/:id'
            element={
              <HRRoute>
                <VacancyPage />
              </HRRoute>
            }
          />
          <Route
            path='/hr/vacancy/:vacancyId/candidate/:candidateId'
            element={
              <HRRoute>
                <VacancyApplicantPage />
              </HRRoute>
            }
          />

          {/* Applicant маршруты */}
          <Route
            path='/applicant'
            element={
              <ApplicantRoute>
                <ApplicantHomePage />
              </ApplicantRoute>
            }
          />
          <Route
            path='/applicant/:vacancyId'
            element={
              <ApplicantRoute>
                <ApplicantVacancyPage />
              </ApplicantRoute>
            }
          />
          <Route
            path='/applicant/about'
            element={
              <ApplicantRoute>
                <AboutPage />
              </ApplicantRoute>
            }
          />

          {/* Публичные маршруты */}
          <Route path='/login' element={<LoginPage />} />
          <Route path='/register' element={<RegisterPage />} />
          <Route path='*' element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default Routing;
