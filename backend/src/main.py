
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.ping.router import router as ping_router
from .api.auth.router import router as auth_router
from .api.applicant.router import router as applicant_router
from .api.hr.router import router as hr_router
from .api.user.router import router as user_router
from .core.database import Base, engine
from dotenv import load_dotenv

load_dotenv()

#* Инициализация базы данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API",
    root_path="/api"
)

origins = os.getenv("ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#* ROUTERS
app.include_router(ping_router)
app.include_router(auth_router, prefix='/auth')
app.include_router(applicant_router, prefix='/applicant')
app.include_router(hr_router, prefix='/hr')
app.include_router(user_router, prefix='/user')