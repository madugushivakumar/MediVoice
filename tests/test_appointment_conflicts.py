import pytest
import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "voice-agent"))

from app.database.connection import SessionLocal, init_db
from app.database.seed import seed_database
from app.services.appointment_service import AppointmentService
from app.database.models import AvailabilitySlot

@pytest.fixture(scope="module")
def db():
    init_db()
    seed_database(reset=True)
    session = SessionLocal()
    yield session
    session.close()

def test_concurrent_booking_simulation(db):
    """
    Simulates two callers attempting to book the exact same slot concurrently.
    The first one must succeed; the second one must be rejected atomically.
    """
    day_3 = (datetime.date.today() + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    avail = AppointmentService.check_doctor_availability(db, doctor_name="Dr. Rajesh Kumar", requested_date=day_3)
    assert avail["success"] is True
    assert len(avail["available_slots"]) > 0
    slot_id = avail["available_slots"][0]["slot_id"]

    # Caller 1 books
    res1 = AppointmentService.book_appointment(db, patient_phone="9811122233", slot_id=slot_id)
    assert res1["success"] is True
    assert res1["status"] == "Booked"

    # Caller 2 attempts to book the same slot
    res2 = AppointmentService.book_appointment(db, patient_phone="9844455566", slot_id=slot_id)
    assert res2["success"] is False
    assert res2["error"] == "SLOT_ALREADY_BOOKED"

    # Verify in DB that only Caller 1's appointment exists for this slot
    slot_db = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).first()
    assert slot_db.status == "Booked"
