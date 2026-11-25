from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Appointment
from app.database.schemas import AppointmentCreateRequest, AppointmentResponse
from app.services.appointment_service import AppointmentService

router = APIRouter(tags=["Appointments"])

@router.get("/appointments", response_model=List[AppointmentResponse])
def get_appointments(
    phone: Optional[str] = Query(None, description="Filter by patient phone"),
    status: Optional[str] = Query(None, description="Filter by status: Booked, Cancelled, Completed"),
    date: Optional[str] = Query(None, description="Filter by appointment date"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    if phone:
        norm_phone = AppointmentService.normalize_phone(phone)
        query = query.filter(Appointment.patient_phone.like(f"%{norm_phone}%"))
    if status:
        query = query.filter(Appointment.status == status)
    if date:
        query = query.filter(Appointment.appointment_date == date)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)

    appts = query.order_by(Appointment.created_at.desc()).all()
    
    results = []
    for a in appts:
        results.append(
            AppointmentResponse(
                id=a.id,
                appointment_id=a.appointment_id,
                patient_phone=AppointmentService.mask_phone(a.patient_phone),
                doctor_id=a.doctor_id,
                doctor_name=a.doctor.name if a.doctor else "Unknown",
                doctor_speciality=a.doctor.speciality if a.doctor else "",
                slot_id=a.slot_id,
                appointment_date=a.appointment_date,
                start_time=a.start_time,
                status=a.status,
                created_at=a.created_at,
                cancelled_at=a.cancelled_at
            )
        )
    return results

@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return AppointmentResponse(
        id=appt.id,
        appointment_id=appt.appointment_id,
        patient_phone=AppointmentService.mask_phone(appt.patient_phone),
        doctor_id=appt.doctor_id,
        doctor_name=appt.doctor.name if appt.doctor else "Unknown",
        doctor_speciality=appt.doctor.speciality if appt.doctor else "",
        slot_id=appt.slot_id,
        appointment_date=appt.appointment_date,
        start_time=appt.start_time,
        status=appt.status,
        created_at=appt.created_at,
        cancelled_at=appt.cancelled_at
    )

@router.post("/appointments")
def create_appointment(
    payload: AppointmentCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    result = AppointmentService.book_appointment(
        db=db,
        patient_phone=payload.patient_phone,
        slot_id=payload.slot_id,
        doctor_id=payload.doctor_id,
        doctor_name=payload.doctor_name,
        appointment_date=payload.appointment_date,
        start_time=payload.start_time
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    return result

@router.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: str,
    phone: str = Body(..., embed=True, description="Patient confirmed phone number"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    result = AppointmentService.cancel_appointment(
        db=db,
        patient_phone=phone,
        appointment_id=appointment_id,
        confirm_cancellation=True
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    return result
