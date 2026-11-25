import logging
from typing import Dict, Any
from pipecat.adapters.llm.services.gemini_adapter import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams
from app.database.connection import SessionLocal
from app.services.appointment_service import AppointmentService

logger = logging.getLogger("medivoice.tools.booking")

BOOKING_TOOL_SCHEMA = FunctionSchema(
    name="book_appointment",
    description="Book an appointment for a caller using their confirmed 10-digit phone number. Only call this tool AFTER the caller has explicitly confirmed their phone number and the appointment details.",
    properties={
        "patient_phone": {
            "type": "string",
            "description": "The caller's confirmed 10-digit mobile number"
        },
        "doctor_name": {
            "type": "string",
            "description": "The name of the selected doctor"
        },
        "doctor_id": {
            "type": "integer",
            "description": "Optional doctor ID if known"
        },
        "slot_id": {
            "type": "integer",
            "description": "Optional slot ID returned from check_doctor_availability"
        },
        "appointment_date": {
            "type": "string",
            "description": "The appointment date (e.g. '2026-11-26' or 'tomorrow')"
        },
        "start_time": {
            "type": "string",
            "description": "The appointment start time (e.g. '10:30 AM')"
        }
    },
    required=["patient_phone"]
)

async def handle_book_appointment(params: FunctionCallParams):
    args = params.arguments
    logger.info(f"Executing tool book_appointment with args (phone masked): {AppointmentService.mask_phone(str(args.get('patient_phone')))}")
    db = SessionLocal()
    try:
        session_id = getattr(params, "tool_call_id", "session")
        result = AppointmentService.book_appointment(
            db=db,
            patient_phone=str(args.get("patient_phone", "")),
            slot_id=args.get("slot_id"),
            doctor_id=args.get("doctor_id"),
            doctor_name=args.get("doctor_name"),
            appointment_date=args.get("appointment_date"),
            start_time=args.get("start_time"),
            session_id=session_id
        )
        await params.result_callback(result)
    except Exception as e:
        logger.error(f"Error in book_appointment: {e}", exc_info=True)
        await params.result_callback({
            "success": False,
            "error": "BOOKING_ERROR",
            "message": f"An error occurred while booking the appointment: {str(e)}"
        })
    finally:
        db.close()
