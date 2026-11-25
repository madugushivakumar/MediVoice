import pytest
import sys
import datetime
from pathlib import Path

# Ensure voice-agent is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "voice-agent"))

from app.database.connection import SessionLocal, init_db
from app.database.seed import seed_database
from app.services.appointment_service import AppointmentService
from app.database.models import Doctor, AvailabilitySlot

@pytest.fixture(scope="module")
def db():
    init_db()
    seed_database(reset=True)
    session = SessionLocal()
    yield session
    session.close()

def test_existing_doctor_availability(db):
    res = AppointmentService.check_doctor_availability(db, doctor_name="Dr. Arjun Reddy")
    assert res["success"] is True
    assert len(res["doctors"]) > 0
    assert res["doctors"][0]["name"] == "Dr. Arjun Reddy"
    assert len(res["available_slots"]) > 0

def test_nonexistent_doctor_availability(db):
    res = AppointmentService.check_doctor_availability(db, doctor_name="Dr. NonExistentGhost")
    assert res["success"] is False
    assert len(res["available_slots"]) == 0
    assert "No active doctors found" in res["message"]

def test_speciality_search(db):
    res = AppointmentService.check_doctor_availability(db, speciality="Cardiology")
    assert res["success"] is True
    assert any("Cardiology" in d["speciality"] for d in res["doctors"])
    assert len(res["available_slots"]) > 0

def test_preferred_time_filter(db):
    res = AppointmentService.check_doctor_availability(db, speciality="Dermatology", preferred_time="02:00 PM")
    assert res["success"] is True
    assert any(s.get("matches_preference") for s in res["available_slots"])

def test_relative_date_parsing():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    assert AppointmentService.parse_relative_date("today") == today_str
    assert AppointmentService.parse_relative_date("tomorrow") == tomorrow_str
