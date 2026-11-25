import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.database.models import Doctor, AvailabilitySlot, Appointment, CallSession
from app.database.schemas import DashboardStatsResponse

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    total_doctors = db.query(Doctor).filter(Doctor.is_active == True).count()
    available_slots = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.status == "Available",
        AvailabilitySlot.appointment_date >= today_str
    ).count()

    today_appointments = db.query(Appointment).filter(
        Appointment.appointment_date == today_str,
        Appointment.status == "Booked"
    ).count()

    active_calls = db.query(CallSession).filter(CallSession.status == "active").count()
    total_appts = db.query(Appointment).count()
    cancelled_appts = db.query(Appointment).filter(Appointment.status == "Cancelled").count()

    return DashboardStatsResponse(
        total_doctors=total_doctors,
        available_slots_count=available_slots,
        today_appointments_count=today_appointments,
        active_calls_count=active_calls,
        total_appointments_count=total_appts,
        cancelled_appointments_count=cancelled_appts
    )
