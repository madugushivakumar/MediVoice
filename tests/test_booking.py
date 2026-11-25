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

def test_successful_booking(db):
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    avail = AppointmentService.check_doctor_availability(db, doctor_name="Dr. Arjun Reddy", requested_date=tomorrow)
    assert avail["success"] is True
    target_slot = avail["available_slots"][0]

    phone = "9876500001"
    booking = AppointmentService.book_appointment(
        db,
        patient_phone=phone,
        slot_id=target_slot["slot_id"]
    )
    assert booking["success"] is True
    assert "APT-" in booking["appointment_id"]
    assert booking["doctor_name"] == "Dr. Arjun Reddy"
    assert booking["status"] == "Booked"

    # Verify slot is now Booked in database
    slot_in_db = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == target_slot["slot_id"]).first()
    assert slot_in_db.status == "Booked"

def test_booking_slot_already_booked(db):
    # Try booking the exact same slot again
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    booked_slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.appointment_date == tomorrow,
        AvailabilitySlot.status == "Booked"
    ).first()
    assert booked_slot is not None

    res = AppointmentService.book_appointment(
        db,
        patient_phone="9876500002",
        slot_id=booked_slot.id
    )
    assert res["success"] is False
    assert res["error"] == "SLOT_ALREADY_BOOKED"

def test_booking_invalid_phone(db):
    res = AppointmentService.book_appointment(
        db,
        patient_phone="12345",  # Invalid short phone
        doctor_name="Dr. Arjun Reddy"
    )
    assert res["success"] is False
    assert res["error"] == "INVALID_PHONE_NUMBER"

def test_booking_invalid_doctor(db):
    res = AppointmentService.book_appointment(
        db,
        patient_phone="9876500003",
        doctor_name="Dr. UnknownDoctor",
        appointment_date="2026-11-26",
        start_time="10:30 AM"
    )
    assert res["success"] is False
    assert res["error"] == "DOCTOR_NOT_FOUND"

def test_duplicate_booking_prevention(db):
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    avail = AppointmentService.check_doctor_availability(db, doctor_name="Dr. Priya Sharma", requested_date=tomorrow)
    slot1 = avail["available_slots"][0]
    slot2 = avail["available_slots"][1]

    phone = "9876543999"
    # First booking succeeds
    b1 = AppointmentService.book_appointment(db, patient_phone=phone, slot_id=slot1["slot_id"])
    assert b1["success"] is True

    # Second booking with same doctor on same day must be rejected as duplicate
    b2 = AppointmentService.book_appointment(db, patient_phone=phone, slot_id=slot2["slot_id"])
    assert b2["success"] is False
    assert b2["error"] == "DUPLICATE_BOOKING"
