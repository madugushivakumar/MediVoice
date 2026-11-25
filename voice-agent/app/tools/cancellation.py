import logging
from typing import Dict, Any
from pipecat.adapters.llm.services.gemini_adapter import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams
from app.database.connection import SessionLocal
from app.services.appointment_service import AppointmentService

logger = logging.getLogger("medivoice.tools.cancellation")

CANCELLATION_TOOL_SCHEMA = FunctionSchema(
    name="cancel_appointment",
    description="Cancel an existing appointment using the caller's confirmed phone number. Requires explicit cancellation confirmation from the caller before execution.",
    properties={
        "patient_phone": {
            "type": "string",
            "description": "The caller's confirmed 10-digit mobile number"
        },
        "appointment_id": {
            "type": "string",
            "description": "Optional specific appointment ID (e.g. 'APT-20261126-ABCD'), required if the caller has multiple active appointments"
        },
        "confirm_cancellation": {
            "type": "boolean",
            "description": "Explicit confirmation that the caller agreed to cancel this appointment"
        }
    },
    required=["patient_phone"]
)

async def handle_cancel_appointment(params: FunctionCallParams):
    args = params.arguments
    logger.info(f"Executing tool cancel_appointment for phone: {AppointmentService.mask_phone(str(args.get('patient_phone')))}")
    db = SessionLocal()
    try:
        session_id = getattr(params, "tool_call_id", "session")
        result = AppointmentService.cancel_appointment(
            db=db,
            patient_phone=str(args.get("patient_phone", "")),
            appointment_id=args.get("appointment_id"),
            confirm_cancellation=args.get("confirm_cancellation", True),
            session_id=session_id
        )
        await params.result_callback(result)
    except Exception as e:
        logger.error(f"Error in cancel_appointment: {e}", exc_info=True)
        await params.result_callback({
            "success": False,
            "error": "CANCELLATION_ERROR",
            "message": f"An error occurred while cancelling the appointment: {str(e)}"
        })
    finally:
        db.close()
