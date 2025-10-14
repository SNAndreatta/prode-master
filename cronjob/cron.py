# app/main.py

from fastapi import FastAPI
import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo
import json
import os

from cronjob.daily_task import update_database

app = FastAPI()

ARG_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
STATE_FILE = "last_run.json"

def load_last_run_datetime() -> datetime | None:
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_run_datetime"])
    except Exception as e:
        print(f"⚠️ Error leyendo el archivo de estado: {e}")
        return None

def save_last_run_datetime(run_datetime: datetime):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_run_datetime": run_datetime.isoformat()}, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error guardando el archivo de estado: {e}")

async def daily_scheduler():
    while True:
        now = datetime.now(ARG_TIMEZONE)
        current_time = now.time()
        today = now.date()

        last_run = load_last_run_datetime()
        last_run_date = last_run.date() if last_run else None

        if current_time >= time(14, 0) and last_run_date != today:
            print(f"🔔 Ejecutando tarea programada a las {now.isoformat()}")
            await update_database(ARG_TIMEZONE, load_last_run_datetime, save_last_run_datetime)
            save_last_run_datetime(now)

        await asyncio.sleep(60)

@app.get("/")
def read_root():
    last_run = load_last_run_datetime()
    return {
        "status": "Servidor activo",
        "ultima_ejecucion": last_run.isoformat() if last_run else "Nunca ejecutado"
    }