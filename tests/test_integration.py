import pytest
import sys
import json
from pathlib import Path
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "voice-agent"))

from app.main import app
from app.database.connection import SessionLocal, init_db
from app.database.seed import seed_database
from app.database.models import Doctor, AvailabilitySlot, Appointment

import os

@pytest.fixture(scope="module")
def client():
    os.environ["TESTING"] = "1"
    init_db()
    seed_database(reset=True)
    with TestClient(app) as c:
        yield c
    os.environ.pop("TESTING", None)

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_doctors_and_specialities(client):
    docs_res = client.get("/api/doctors")
    assert docs_res.status_code == 200
    doctors = docs_res.json()
    assert len(doctors) == 8

    specs_res = client.get("/api/specialities")
    assert specs_res.status_code == 200
    specialities = specs_res.json()
    assert "Cardiology" in specialities
    assert "Dermatology" in specialities

def test_dashboard_stats(client):
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_doctors"] == 8
    assert data["available_slots_count"] > 0

def test_voice_call_session_start_and_websocket_greeting(client):
    # 1. Start call session
    start_res = client.post("/api/calls/start")
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert "call_" in session_id

    # 2. Connect to voice WebSocket
    with client.websocket_connect(f"/ws/call/{session_id}") as ws:
        # First message: CALL_STATE_CHANGED (CONNECTED)
        state_msg = json.loads(ws.receive_text())
        assert state_msg["type"] == "CALL_STATE_CHANGED"
        assert state_msg["data"]["state"] == "CONNECTED"

        # Second message: PIPELINE_MODE
        mode_msg = json.loads(ws.receive_text())
        assert mode_msg["type"] == "PIPELINE_MODE"

        # Third message: TRANSCRIPT_UPDATE (AI initial greeting)
        greeting_msg = json.loads(ws.receive_text())
        assert greeting_msg["type"] == "TRANSCRIPT_UPDATE"
        assert greeting_msg["data"]["speaker"] == "AI"
        assert "MediVoice Healthcare Clinic" in greeting_msg["data"]["message"]

def test_full_conversational_booking_workflow(client):
    """
    Test 2 from Final Acceptance Criteria:
    Caller speaks intent -> AI checks availability -> Caller chooses slot ->
    Caller speaks phone -> AI repeats digit by digit -> Caller confirms ->
    AI confirms booking details -> Caller authorizes -> AI calls book_appointment ->
    Database saves appointment -> Slot becomes unavailable.
    """
    start_res = client.post("/api/calls/start")
    session_id = start_res.json()["session_id"]

    with client.websocket_connect(f"/ws/call/{session_id}") as ws:
        # Read initial state, pipeline mode & greeting
        ws.receive_text() # state
        ws.receive_text() # mode
        ws.receive_text() # greeting

        # Step 1: Caller speaks enquiry about cardiologist tomorrow
        ws.send_text(json.dumps({
            "type": "USER_SPEECH",
            "text": "Hello, I need an appointment with a cardiologist tomorrow"
        }))

        # Read caller transcript confirmation
        caller_t1 = json.loads(ws.receive_text())
        assert caller_t1["data"]["speaker"] == "Caller"

        # Read state change to THINKING
        state_thinking = json.loads(ws.receive_text())
        assert state_thinking["data"]["state"] == "THINKING"

        # Read tool executed event (check_doctor_availability)
        tool_ev1 = json.loads(ws.receive_text())
        assert tool_ev1["type"] == "TOOL_EXECUTED"
        assert tool_ev1["data"]["tool"] == "check_doctor_availability"
        assert tool_ev1["data"]["result"]["success"] is True

        # Read state change to SPEAKING
        ws.receive_text()

        # Read AI response offering available slots
        ai_resp1 = json.loads(ws.receive_text())
        assert "Arjun Reddy" in ai_resp1["data"]["message"]
        assert "Which time would you prefer" in ai_resp1["data"]["message"]

        # Read synthetic audio bytes
        ws.receive_bytes()

        # Read state change back to CONNECTED
        ws.receive_text()

        # Step 2: Caller chooses time 10:30 AM
        ws.send_text(json.dumps({
            "type": "USER_SPEECH",
            "text": "I want the 10:30 AM slot"
        }))
        ws.receive_text() # caller transcript
        ws.receive_text() # THINKING
        ws.receive_text() # SPEAKING
        ai_resp2 = json.loads(ws.receive_text())
        assert "May I have your 10-digit mobile number" in ai_resp2["data"]["message"]
        ws.receive_bytes() # audio
        ws.receive_text() # CONNECTED

        # Step 3: Caller speaks phone number 9876500099
        ws.send_text(json.dumps({
            "type": "USER_SPEECH",
            "text": "9876500099"
        }))
        ws.receive_text() # caller transcript
        ws.receive_text() # THINKING
        ws.receive_text() # SPEAKING
        ai_resp3 = json.loads(ws.receive_text())
        # AI MUST repeat digit-by-digit
        assert "9-8-7-6-5-0-0-0-9-9" in ai_resp3["data"]["message"]
        assert "Is that correct" in ai_resp3["data"]["message"]
        ws.receive_bytes() # audio
        ws.receive_text() # CONNECTED

        # Step 4: Caller confirms phone readback
        ws.send_text(json.dumps({
            "type": "USER_SPEECH",
            "text": "Yes, that is correct"
        }))
        ws.receive_text() # caller transcript
        ws.receive_text() # THINKING
        ws.receive_text() # SPEAKING
        ai_resp4 = json.loads(ws.receive_text())
        # AI summarizes booking details and asks for final authorization
        assert "Shall I confirm this appointment" in ai_resp4["data"]["message"]
        assert "0099" in ai_resp4["data"]["message"]
        ws.receive_bytes() # audio
        ws.receive_text() # CONNECTED

        # Step 5: Caller authorizes booking
        ws.send_text(json.dumps({
            "type": "USER_SPEECH",
            "text": "Yes, please book it"
        }))
        ws.receive_text() # caller transcript
        ws.receive_text() # THINKING
        
        # Tool executed: book_appointment
        tool_ev2 = json.loads(ws.receive_text())
        assert tool_ev2["type"] == "TOOL_EXECUTED"
        assert tool_ev2["data"]["tool"] == "book_appointment"
        assert tool_ev2["data"]["result"]["success"] is True

        ws.receive_text() # SPEAKING
        ai_resp5 = json.loads(ws.receive_text())
        assert "successfully booked" in ai_resp5["data"]["message"]
        assert "APT-" in ai_resp5["data"]["message"]

        # Step 6: Verify in Database
        db = SessionLocal()
        appt = db.query(Appointment).filter(Appointment.patient_phone == "9876500099").first()
        assert appt is not None
        assert appt.status == "Booked"
        
        # Verify slot is marked Booked
        slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == appt.slot_id).first()
        assert slot.status == "Booked"
        db.close()
