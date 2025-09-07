from sqlalchemy import Column, Enum, Integer, String, Numeric, DateTime, ForeignKey, Text, Boolean, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

JobApplicationStatusEnum = Enum('cvReview', 'interview', 'waitResult', 'rejected', 'approved', name='job_application_status_enum')
VacancyStatusEnum = Enum('active', 'closed', 'stopped', name='vacancy_status_enum')
RoleEnum = Enum('hr', 'applicant', name='role_enum')
ReqTypeEnum = Enum('reject', 'next', name='req_type_enum')
MeetingStatusEnum = Enum('cvReview', 'waitPickTime', 'waitMeeting', 'waitResult', 'rejected', 'approved', name='meeting_status_enum')
OfferTypeEnum = Enum('TK', 'GPH', 'IP', name='offer_type_enum')
BusyTypeEnum = Enum('allTime', 'projectTime', name='busy_type_enum')

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
    region = Column(String)
    city = Column(String)
    address = Column(String)
    offerType = Column(OfferTypeEnum)
    busyType = Column(BusyTypeEnum)
    graph = Column(String)
    salaryMin = Column(Numeric)
    salaryMax = Column(Numeric)
    annualBonus = Column(Numeric)
    bonusType = Column(String)  
    description = Column(Text)  
    prompt = Column(Text) 
    exp = Column(Integer)  
    degree = Column(Boolean)  
    specialSoftware = Column(String)  
    computerSkills = Column(String) 
    foreignLanguages = Column(String) 
    languageLevel = Column(String)
    businessTrips = Column(Boolean)

    hr_profile = relationship("HRProfile", back_populates="vacancies")
    job_applications = relationship("JobApplication", back_populates="vacancy")
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
    job_applications = relationship("JobApplication", back_populates="applicant_profile")
    resume_versions = relationship(
        "ApplicantResumeVersion",
        back_populates="applicant",
        cascade="all, delete-orphan",
        order_by="ApplicantResumeVersion.created_at.desc()",
    )

class JobApplication(Base):
    __tablename__ = 'job_applications'

    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=True)
    applicant_id = Column(Integer, ForeignKey('applicant_profiles.id'))
    resume_version_id = Column(
        Integer,
        ForeignKey('applicant_resume_versions.id', ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(JobApplicationStatusEnum)
    contacts = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    vacancy = relationship("Vacancy", back_populates="job_applications")
    applicant_profile = relationship("ApplicantProfile", back_populates="job_applications")
    job_application_events = relationship("JobApplicationEvent", back_populates="job_application", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="job_application", cascade="all, delete-orphan")
    resume_version = relationship("ApplicantResumeVersion")
    cv_evaluations = relationship(
        "JobApplicationCVEvaluation",
        back_populates="job_application",
        cascade="all, delete-orphan"
    )

class JobApplicationCVEvaluation(Base):
    __tablename__ = 'job_application_cv_evaluations'

    id = Column(Integer, primary_key=True)
    job_application_id = Column(Integer, ForeignKey('job_applications.id', ondelete="CASCADE"), nullable=False)
    resume_version_id = Column(Integer, ForeignKey('applicant_resume_versions.id', ondelete="CASCADE"), nullable=False)

    model = Column(String(64), nullable=False) 

    name = Column(String, nullable=False) 
    score = Column(Integer, nullable=False) 
    strengths = Column(ARRAY(String), nullable=False, server_default=text("'{}'::text[]"))
    weaknesses = Column(ARRAY(String), nullable=False, server_default=text("'{}'::text[]"))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    job_application = relationship("JobApplication", back_populates="cv_evaluations")
    resume_version = relationship("ApplicantResumeVersion")

class JobApplicationEvent(Base):
    __tablename__ = 'job_application_events'

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('job_applications.id'))
    reqType = Column(ReqTypeEnum)
    status = Column(JobApplicationStatusEnum)
    created_at = Column(DateTime, server_default=func.now())

    job_application = relationship("JobApplication", back_populates="job_application_events")

class ApplicantResumeVersion(Base):
    __tablename__ = 'applicant_resume_versions'

    id = Column(Integer, primary_key=True)
    applicant_id = Column(Integer, ForeignKey('applicant_profiles.id', ondelete="CASCADE"), nullable=False)

    storage_path = Column(String, nullable=False)
    text_hash = Column(String(64))  
    is_current = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    applicant = relationship("ApplicantProfile", back_populates="resume_versions")


class Meeting(Base):
    __tablename__ = 'meetings'

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('job_applications.id')) 
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=True)
    status = Column(MeetingStatusEnum)
    hrContact = Column(String)
    meetLink = Column(String)
    calendarLink = Column(String)
    
    created_at = Column(DateTime, server_default=func.now()) 

    job_application = relationship("JobApplication", back_populates="meetings")
    vacancy = relationship("Vacancy", back_populates="meetings")