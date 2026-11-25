import logging
from typing import Dict, Any, List
from pipecat.services.google.llm import GoogleLLMService
from app.config.settings import settings
from app.agents.system_prompt import get_system_prompt
from app.tools.availability import AVAILABILITY_TOOL_SCHEMA, handle_check_doctor_availability
from app.tools.booking import BOOKING_TOOL_SCHEMA, handle_book_appointment
from app.tools.cancellation import CANCELLATION_TOOL_SCHEMA, handle_cancel_appointment

logger = logging.getLogger("medivoice.agent")

class DoctorAssistantAgent:
    @staticmethod
    def create_llm_service() -> GoogleLLMService:
        """
        Creates and configures the Google Gemini LLM service with all 3 required tools registered.
        Adapts tool schemas into the function_declarations structure required by the Google GenAI SDK.
        """
        system_instruction = get_system_prompt()
        
        # Define all 3 tools in the function_declarations format expected by Google GenAI
        function_declarations = [
            AVAILABILITY_TOOL_SCHEMA.to_default_dict(),
            BOOKING_TOOL_SCHEMA.to_default_dict(),
            CANCELLATION_TOOL_SCHEMA.to_default_dict()
        ]
        tools = [{"function_declarations": function_declarations}]

        llm = GoogleLLMService(
            api_key=settings.GEMINI_API_KEY or "dummy_key",
            model=settings.GEMINI_MODEL,
            system_instruction=system_instruction,
            tools=tools
        )

        # Register function handlers
        llm.register_function("check_doctor_availability", handle_check_doctor_availability)
        llm.register_function("book_appointment", handle_book_appointment)
        llm.register_function("cancel_appointment", handle_cancel_appointment)

        logger.info("DoctorAssistantAgent initialized with Gemini LLM and 3 appointment tools.")
        return llm
