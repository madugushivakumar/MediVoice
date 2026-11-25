"""
MediVoice Bot - Standalone Runner & Voice Agent Verification
"""
import asyncio
import logging
from app.config.settings import settings
from app.agents.doctor_assistant import DoctorAssistantAgent
from app.database.connection import init_db
from app.database.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medivoice.bot")

def main():
    logger.info("Initializing MediVoice Bot environment...")
    init_db()
    seed_database(reset=False)
    llm = DoctorAssistantAgent.create_llm_service()
    logger.info(f"MediVoice Bot initialized with Gemini model '{settings.GEMINI_MODEL}' and appointment tools.")

if __name__ == "__main__":
    main()
