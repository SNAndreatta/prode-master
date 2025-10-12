import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from contextlib import asynccontextmanager

# FOOTBALL-API
from blueprints.api_football.countries import countries_router_AF
from blueprints.api_football.leagues import leagues_router_AF
from blueprints.api_football.teams import teams_router_AF
from blueprints.api_football.fixtures import fixtures_router_AF
from blueprints.api_football.round import rounds_router_AF

# API
from blueprints.api.countries import countries_router
from blueprints.api.leagues import leagues_router
from blueprints.api.fixtures import fixtures_router
"""from blueprints.api.teams.router import teams_router"""

from core.api_connection import apiFutbolServicio
import os

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

# FOOTBALL-API
app.include_router(countries_router_AF)
app.include_router(leagues_router_AF)
app.include_router(teams_router_AF)
app.include_router(fixtures_router_AF)
app.include_router(rounds_router_AF)