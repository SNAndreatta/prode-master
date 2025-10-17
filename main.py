import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from contextlib import asynccontextmanager
import asyncio
from cronjob.cron import daily_scheduler

# API
from blueprints.api.countries import countries_router
from blueprints.api.leagues import leagues_router
from blueprints.api.fixtures import fixtures_router

# Auth
from blueprints.auth.auth_routes import auth_router

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

origins = [
    "http://localhost:5173",  
]

api_endpoint = os.getenv("API_ENDPOINT")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tablas creadas exitosamente.")
        print("Intentando iniciar tarea programada")
        asyncio.create_task(daily_scheduler())
    yield
    print("Aplicación cerrada.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,    
    allow_methods=["*"],        
    allow_headers=["*"],        
)

# CRUD-API
app.include_router(countries_router)
app.include_router(leagues_router)
app.include_router(fixtures_router)
app.include_router(auth_router)