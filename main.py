import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from blueprints.countries.countries import countries_router

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

origins = [
    "http://localhost:5173",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,    
    allow_methods=["*"],        
    allow_headers=["*"],        
)

app.include_router(countries_router)