import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.connection import init_db
from app.database.seed import seed_database
from app.api.routes import doctors, availability, appointments, dashboard, calls
from app.api.websocket import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medivoice")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MediVoice Database and Services...")
    init_db()
    seed_database(reset=False)
    logger.info("MediVoice Backend is ready.")
    yield
    logger.info("MediVoice Backend shutting down.")

app = FastAPI(
    title="MediVoice - AI Voice Doctor Appointment Assistant",
    description="Real-Time Voice AI Backend with Pipecat, Gemini LLM, ElevenLabs STT/TTS & SQLite",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - avoid wildcard when credentials enabled
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routers
app.include_router(calls.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")
app.include_router(availability.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# Register WebSockets
app.include_router(ws_router)

# Mount Voice Pipeline Router (imported dynamically or registered)
try:
    from app.pipeline import voice_router
    app.include_router(voice_router)
    logger.info("Mounted real-time Pipecat voice pipeline router.")
except ImportError:
    logger.info("Voice pipeline router will be mounted once pipeline.py is loaded.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
