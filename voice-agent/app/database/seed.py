import os
import json
import datetime
from pathlib import Path
from app.database.connection import SessionLocal, init_db
from app.database.models import Doctor, AvailabilitySlot, Appointment, CallSession, ConversationMessage, ToolExecutionLog

def seed_database(reset: bool = False):
    init_db()
    db = SessionLocal()
    try:
        if reset:
            db.query(ConversationMessage).delete()
            db.query(CallSession).delete()
            db.query(ToolExecutionLog).delete()
            db.query(Appointment).delete()
            db.query(AvailabilitySlot).delete()
            db.query(Doctor).delete()
            db.commit()

        # Check if doctors already exist
        existing_doctors = db.query(Doctor).count()
        if existing_doctors > 0 and not reset:
            print("Database already contains doctor data. Skipping seed to prevent overwrite.")
            return

        # Load seed data json
        data_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "seed_data.json"
        if not data_path.exists():
            data_path = Path("data/seed_data.json")

        with open(data_path, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        doctors_map = {}
        for doc_item in seed_data["doctors"]:
            doc = Doctor(
                name=doc_item["name"],
                speciality=doc_item["speciality"],
                qualification=doc_item["qualification"],
                experience_years=doc_item["experience_years"],
                department=doc_item["department"],
                consultation_duration=doc_item["consultation_duration"],
                is_active=doc_item["is_active"]
            )
            db.add(doc)
            db.flush()
            doctors_map[doc.name] = doc

        # Generate slots for today and next 7 days
        # Times: 09:30 AM, 10:30 AM, 11:30 AM, 02:00 PM, 03:00 PM, 04:30 PM
        standard_times = [
            ("09:30 AM", "10:00 AM"),
            ("10:30 AM", "11:00 AM"),
            ("11:30 AM", "12:00 PM"),
            ("02:00 PM", "02:30 PM"),
            ("03:00 PM", "03:30 PM"),
            ("04:30 PM", "05:00 PM")
        ]

        today = datetime.date.today()
        slots_created = []

        for doc_name, doc in doctors_map.items():
            for day_offset in range(8):  # today + 7 days
                slot_date = (today + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
                for start_t, end_t in standard_times:
                    slot = AvailabilitySlot(
                        doctor_id=doc.id,
                        appointment_date=slot_date,
                        start_time=start_t,
                        end_time=end_t,
                        status="Available"
                    )
                    db.add(slot)
                    slots_created.append(slot)

        db.flush()

        # Seed sample booked appointments
        for appt_spec in seed_data.get("sample_appointments", []):
            doc = doctors_map.get(appt_spec["doctor_name"])
            if not doc:
                continue
            appt_date = (today + datetime.timedelta(days=appt_spec["date_offset_days"])).strftime("%Y-%m-%d")
            # Find matching slot
            slot = db.query(AvailabilitySlot).filter(
                AvailabilitySlot.doctor_id == doc.id,
                AvailabilitySlot.appointment_date == appt_date,
                AvailabilitySlot.start_time == appt_spec["start_time"]
            ).first()

            if slot:
                slot.status = "Booked"
                short_hash = os.urandom(2).hex().upper()
                appt_id = f"APT-{appt_date.replace('-', '')}-{short_hash}"
                appointment = Appointment(
                    appointment_id=appt_id,
                    patient_phone=appt_spec["patient_phone"],
                    doctor_id=doc.id,
                    slot_id=slot.id,
                    appointment_date=appt_date,
                    start_time=slot.start_time,
                    status="Booked",
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
                )
                db.add(appointment)

        db.commit()
        print(f"Database successfully seeded with {len(doctors_map)} doctors and slots!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database(reset=True)
