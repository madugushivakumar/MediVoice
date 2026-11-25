from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.appointment_service import AppointmentService

router = APIRouter(tags=["Availability"])

@router.get("/availability")
def get_availability(
    doctor_name: Optional[str] = Query(None, description="Doctor name to filter"),
    speciality: Optional[str] = Query(None, description="Speciality to filter"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD or 'today'/'tomorrow'"),
    preferred_time: Optional[str] = Query(None, description="Preferred time or period"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    return AppointmentService.check_doctor_availability(
        db=db,
        doctor_name=doctor_name,
        speciality=speciality,
        requested_date=date,
        preferred_time=preferred_time
    )
