import pytest
import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "voice-agent"))

from app.database.connection import SessionLocal, init_db
from app.database.seed import seed_database
from app.services.appointment_service import AppointmentService
from app.database.models import AvailabilitySlot, Appointment

@pytest.fixture(scope="module")
def db():
    init_db()
    seed_database(reset=True)
    session = SessionLocal()
    yield session
    session.close()

def test_successful_cancellation(db):
    # Seed data has an appointment for 9123456780
    phone = "9123456780"
    appts = db.query(Appointment).filter(Appointment.patient_phone == phone, Appointment.status == "Booked").all()
    assert len(appts) == 1
    target = appts[0]
    slot_id = target.slot_id

    # Verify slot is currently booked
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).first()
    assert slot.status == "Booked"

    # Cancel appointment
    res = AppointmentService.cancel_appointment(db, patient_phone=phone, appointment_id=target.appointment_id)
    assert res["success"] is True
    assert res["status"] == "Cancelled"

    # Verify DB status updated
    db.refresh(target)
    assert target.status == "Cancelled"
    assert target.cancelled_at is not None

    # Verify slot has been released back to Available
    db.refresh(slot)
    assert slot.status == "Available"

def test_cancellation_unknown_phone(db):
    res = AppointmentService.cancel_appointment(db, patient_phone="9999999999")
    assert res["success"] is False
    assert res["error"] == "NO_APPOINTMENTS_FOUND"

def test_multiple_appointments_selection(db):
    # Seed data has 2 appointments for 9876543210
    phone = "9876543210"
    res = AppointmentService.cancel_appointment(db, patient_phone=phone)
    assert res["success"] is False
    assert res["error"] == "MULTIPLE_APPOINTMENTS"
    assert res["requires_selection"] is True
    assert len(res["appointments"]) >= 2
