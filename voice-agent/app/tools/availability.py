import logging
from typing import Dict, Any
from pipecat.adapters.llm.services.gemini_adapter import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams
from app.database.connection import SessionLocal
from app.services.appointment_service import AppointmentService

logger = logging.getLogger("medivoice.tools.availability")

# Schema for Gemini LLM
AVAILABILITY_TOOL_SCHEMA = FunctionSchema(
    name="check_doctor_availability",
    description="Check doctor availability and return actual available appointment slots for a doctor, speciality, or requested date. Never invents available slots.",
    properties={
        "doctor_name": {
            "type": "string",
            "description": "Optional name of the doctor (e.g. 'Dr. Arjun Reddy' or 'Arjun')"
        },
        "speciality": {
            "type": "string",
            "description": "Optional medical speciality (e.g. 'Cardiology', 'Dermatology', 'Neurology', 'Pediatrics')"
        },
        "requested_date": {
            "type": "string",
            "description": "Requested date, e.g. 'today', 'tomorrow', 'November 26', or 'YYYY-MM-DD'"
        },
        "preferred_time": {
            "type": "string",
            "description": "Optional preferred time or period, e.g. '10:30 AM', 'morning', 'afternoon'"
        }
    },
    required=[]
)

async def handle_check_doctor_availability(params: FunctionCallParams):
    args = params.arguments
    logger.info(f"Executing tool check_doctor_availability with args: {args}")
    db = SessionLocal()
    try:
        doctor_name = args.get("doctor_name")
        speciality = args.get("speciality")
        requested_date = args.get("requested_date")
        preferred_time = args.get("preferred_time")

        session_id = getattr(params, "tool_call_id", "session")
        result = AppointmentService.check_doctor_availability(
            db=db,
            doctor_name=doctor_name,
            speciality=speciality,
            requested_date=requested_date,
            preferred_time=preferred_time,
            session_id=session_id
        )
        await params.result_callback(result)
    except Exception as e:
        logger.error(f"Error in check_doctor_availability: {e}", exc_info=True)
        await params.result_callback({
            "success": False,
            "error": "TOOL_ERROR",
            "message": f"Failed to check doctor availability: {str(e)}"
        })
    finally:
        db.close()
