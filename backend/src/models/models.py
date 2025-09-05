from sqlalchemy import Column, Enum, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

StatusEnum = Enum('review', 'screening', 'result', 'reject', 'approve', name='status_enum')
VacancyStatusEnum = Enum('hold', 'found', 'approve', name='vacancy_status_enum')
RoleEnum = Enum('hr', 'applicant', name='role_enum')
ReqTypeEnum = Enum('reject', 'next', name='req_type_enum')
MeetingStatusEnum = Enum('cvReview', 'waitPickTime', 'waitMeeting', 'waitResult', 'reject', 'approve', name='meeting_status_enum')

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(RoleEnum)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    hr_profile = relationship("HRProfile", back_populates="user", uselist=False)
    applicant_profile = relationship("ApplicantProfile", back_populates="user", uselist=False)

class HRProfile(Base):
    __tablename__ = 'hr_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    surname = Column(String)
    patronymic = Column(String)
    department = Column(String)
    contacts = Column(String)

    user = relationship("User", back_populates="hr_profile")
    vacancies = relationship("Vacancy", back_populates="hr_profile")

class Vacancy(Base):
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True)
    hr_id = Column(Integer, ForeignKey('hr_profiles.id'))
    name = Column(String)
    department = Column(String)
    status = Column(VacancyStatusEnum)
    date = Column(DateTime)

    hr_profile = relationship("HRProfile", back_populates="vacancies")
    applications = relationship("Application", back_populates="vacancy")
    meetings = relationship("Meeting", back_populates="vacancy")

class ApplicantProfile(Base):
    __tablename__ = 'applicant_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    surname = Column(String)
    patronymic = Column(String)
    contacts = Column(String)
    cv = Column(Text)
    summary = Column(Text)

    user = relationship("User", back_populates="applicant_profile")
    applications = relationship("Application", back_populates="applicant_profile")

class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=True)
    applicant_id = Column(Integer, ForeignKey('applicant_profiles.id'))
    status = Column(StatusEnum)
    soft = Column(Numeric)
    tech = Column(Numeric)
    salary = Column(Numeric)
    contacts = Column(String)
    sumGrade = Column(Numeric)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    vacancy = relationship("Vacancy", back_populates="applications")
    applicant_profile = relationship("ApplicantProfile", back_populates="applications")
    application_events = relationship("ApplicationEvent", back_populates="application")
    meetings = relationship("Meeting", back_populates="application")

class ApplicationEvent(Base):
    __tablename__ = 'application_events'

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('applications.id'))
    reqType = Column(ReqTypeEnum)
    status = Column(StatusEnum)
    created_at = Column(DateTime, server_default=func.now())

    application = relationship("Application", back_populates="application_events")

class Meeting(Base):
    __tablename__ = 'meetings'

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('applications.id')) 
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=True)
    status = Column(MeetingStatusEnum)
    hrContact = Column(String)
    meetLink = Column(String)
    calendarLink = Column(String)
    
    application = relationship("Application", back_populates="meetings")
    vacancy = relationship("Vacancy", back_populates="meetings")