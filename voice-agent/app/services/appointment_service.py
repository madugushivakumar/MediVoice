import os
import re
import datetime
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database.models import Doctor, AvailabilitySlot, Appointment, ToolExecutionLog
from app.services.doctor_service import DoctorService
from app.services.event_service import event_service

class AppointmentService:
    @staticmethod
    def mask_phone(phone: str) -> str:
        if not phone:
            return ""
        clean = re.sub(r"\D", "", phone)
        if len(clean) >= 4:
            return f"{'*' * (len(clean) - 4)}{clean[-4:]}"
        return clean

    @staticmethod
    def normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)
        # Handle country code like +91 or 91 with 10 digits
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) > 10 and digits.startswith("0"):
            digits = digits[1:]
        return digits

    @staticmethod
    def validate_phone(phone: str) -> bool:
        norm = AppointmentService.normalize_phone(phone)
        # Indian standard mobile number: 10 digits starting with 6, 7, 8, or 9
        return len(norm) == 10 and norm[0] in "6789"

    @staticmethod
    def parse_relative_date(date_str: str) -> str:
        """Helper to resolve 'today', 'tomorrow', 'day after tomorrow' or natural dates."""
        today = datetime.date.today()
        if not date_str:
            return today.strftime("%Y-%m-%d")
        
        lowered = date_str.lower().strip()
        if "today" in lowered:
            return today.strftime("%Y-%m-%d")
        elif "tomorrow" in lowered and "day after" not in lowered:
            return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif "day after tomorrow" in lowered:
            return (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

        # Try common formats
        date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"]
        for fmt in date_formats:
            try:
                parsed = datetime.datetime.strptime(lowered, fmt).date()
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # If year is omitted e.g. "November 26"
        for fmt in ["%B %d", "%b %d", "%d %B", "%d %b"]:
            try:
                parsed = datetime.datetime.strptime(lowered, fmt).date()
                parsed = parsed.replace(year=today.year)
                if parsed < today:
                    parsed = parsed.replace(year=today.year + 1)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return lowered

    # =========================================================================
    # TOOL 1: check_doctor_availability
    # =========================================================================
    @staticmethod
    def check_doctor_availability(
        db: Session,
        doctor_name: Optional[str] = None,
        speciality: Optional[str] = None,
        requested_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search doctors by name or speciality, filter by date and preferred time.
        Never invents available slots. Never returns booked or expired slots as available.
        """
        parsed_date = AppointmentService.parse_relative_date(requested_date) if requested_date else datetime.date.today().strftime("%Y-%m-%d")
        
        # Query doctor candidates
        doc_query = db.query(Doctor).filter(Doctor.is_active == True)
        if doctor_name:
            clean_doc = doctor_name.lower().replace("dr.", "").replace("dr", "").strip()
            doc_query = doc_query.filter(Doctor.name.ilike(f"%{clean_doc}%"))
        if speciality:
            doc_query = doc_query.filter(Doctor.speciality.ilike(f"%{speciality.strip()}%"))

        matched_doctors = doc_query.all()
        if not matched_doctors:
            result = {
                "success": False,
                "message": f"No active doctors found matching name '{doctor_name or ''}' or speciality '{speciality or ''}'.",
                "doctors": [],
                "available_slots": [],
                "date": parsed_date
            }
            AppointmentService._log_tool(db, session_id, "check_doctor_availability", locals(), result, "failure")
            return result

        doc_ids = [d.id for d in matched_doctors]
        
        # Query slots strictly marked Available
        slot_query = db.query(AvailabilitySlot).filter(
            AvailabilitySlot.doctor_id.in_(doc_ids),
            AvailabilitySlot.appointment_date == parsed_date,
            AvailabilitySlot.status == "Available"
        )

        slots = slot_query.order_by(AvailabilitySlot.doctor_id, AvailabilitySlot.start_time).all()

        doctor_dict = {d.id: d for d in matched_doctors}
        available_slots = []
        for s in slots:
            doc = doctor_dict.get(s.doctor_id)
            slot_info = {
                "slot_id": s.id,
                "doctor_id": s.doctor_id,
                "doctor_name": doc.name if doc else "Unknown",
                "speciality": doc.speciality if doc else "",
                "date": s.appointment_date,
                "start_time": s.start_time,
                "end_time": s.end_time
            }
            if preferred_time:
                # If preferred time matches (e.g. morning, 10:30, PM)
                pref = preferred_time.lower().strip()
                if pref in s.start_time.lower() or (pref == "morning" and "am" in s.start_time.lower()) or (pref == "afternoon" and "pm" in s.start_time.lower()):
                    slot_info["matches_preference"] = True
            available_slots.append(slot_info)

        doctors_summary = [
            {
                "doctor_id": d.id,
                "name": d.name,
                "speciality": d.speciality,
                "qualification": d.qualification,
                "experience_years": d.experience_years,
                "department": d.department,
                "slots_count": len([s for s in available_slots if s["doctor_id"] == d.id])
            }
            for d in matched_doctors
        ]

        result = {
            "success": True,
            "message": f"Found {len(available_slots)} available slot(s) across {len(matched_doctors)} doctor(s) for {parsed_date}.",
            "date": parsed_date,
            "doctors": doctors_summary,
            "available_slots": available_slots
        }

        AppointmentService._log_tool(db, session_id, "check_doctor_availability", {"doctor_name": doctor_name, "speciality": speciality, "date": parsed_date}, result, "success")
        return result

    # =========================================================================
    # TOOL 2: book_appointment
    # =========================================================================
    @staticmethod
    def book_appointment(
        db: Session,
        patient_phone: str,
        slot_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        doctor_name: Optional[str] = None,
        appointment_date: Optional[str] = None,
        start_time: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Atomic booking of an appointment.
        Validates slot, checks availability, prevents double bookings, saves in DB.
        """
        normalized_phone = AppointmentService.normalize_phone(patient_phone)
        if not AppointmentService.validate_phone(normalized_phone):
            result = {
                "success": False,
                "error": "INVALID_PHONE_NUMBER",
                "message": f"Invalid phone number provided. Must be a valid 10-digit mobile number."
            }
            AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(patient_phone)}, result, "failure")
            return result

        # Resolve slot
        slot = None
        if slot_id:
            slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).with_for_update().first()
        elif (doctor_id or doctor_name) and appointment_date and start_time:
            parsed_date = AppointmentService.parse_relative_date(appointment_date)
            doc = None
            if doctor_id:
                doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
            elif doctor_name:
                doc = DoctorService.get_doctor_by_name(db, doctor_name)
            
            if not doc:
                result = {
                    "success": False,
                    "error": "DOCTOR_NOT_FOUND",
                    "message": f"Doctor '{doctor_name or doctor_id}' not found."
                }
                AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(patient_phone)}, result, "failure")
                return result

            # Normalize start_time comparison
            slot = db.query(AvailabilitySlot).filter(
                AvailabilitySlot.doctor_id == doc.id,
                AvailabilitySlot.appointment_date == parsed_date,
                AvailabilitySlot.start_time.ilike(f"%{start_time.strip()}%")
            ).with_for_update().first()

        if not slot:
            result = {
                "success": False,
                "error": "SLOT_NOT_FOUND",
                "message": "The requested appointment slot could not be found."
            }
            AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(patient_phone)}, result, "failure")
            return result

        # Check atomic availability
        if slot.status != "Available":
            result = {
                "success": False,
                "error": "SLOT_ALREADY_BOOKED",
                "message": f"Sorry, the {slot.start_time} slot on {slot.appointment_date} has already been booked. Please choose another slot."
            }
            AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(patient_phone), "slot_id": slot.id}, result, "failure")
            return result

        # Check duplicate booking by same caller for same slot or doctor on same day
        existing_dup = db.query(Appointment).filter(
            Appointment.patient_phone == normalized_phone,
            Appointment.doctor_id == slot.doctor_id,
            Appointment.appointment_date == slot.appointment_date,
            Appointment.status == "Booked"
        ).first()

        if existing_dup:
            result = {
                "success": False,
                "error": "DUPLICATE_BOOKING",
                "message": f"You already have an active appointment (ID: {existing_dup.appointment_id}) with this doctor on {slot.appointment_date} at {existing_dup.start_time}."
            }
            AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(patient_phone)}, result, "failure")
            return result

        try:
            # Atomic state transition
            slot.status = "Booked"
            doc = db.query(Doctor).filter(Doctor.id == slot.doctor_id).first()
            date_part = slot.appointment_date.replace("-", "")
            rand_hex = os.urandom(2).hex().upper()
            appt_id = f"APT-{date_part}-{rand_hex}"

            new_appt = Appointment(
                appointment_id=appt_id,
                patient_phone=normalized_phone,
                doctor_id=slot.doctor_id,
                slot_id=slot.id,
                appointment_date=slot.appointment_date,
                start_time=slot.start_time,
                status="Booked",
                created_at=datetime.datetime.utcnow()
            )
            db.add(new_appt)
            db.commit()
            db.refresh(new_appt)

            confirmation = {
                "success": True,
                "appointment_id": new_appt.appointment_id,
                "doctor_id": doc.id,
                "doctor_name": doc.name,
                "speciality": doc.speciality,
                "appointment_date": new_appt.appointment_date,
                "start_time": new_appt.start_time,
                "patient_phone_masked": AppointmentService.mask_phone(normalized_phone),
                "status": "Booked",
                "message": f"Appointment successfully booked with {doc.name} for {new_appt.appointment_date} at {new_appt.start_time}. Confirmation ID is {new_appt.appointment_id}."
            }

            AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(normalized_phone), "slot_id": slot.id}, confirmation, "success")
            
            # Broadcast live update
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(event_service.broadcast("APPOINTMENT_BOOKED", confirmation))
            except Exception:
                pass

            return confirmation

        except Exception as e:
            db.rollback()
            result = {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": f"Failed to book appointment due to a database conflict: {str(e)}"
            }
            AppointmentService._log_tool(db, session_id, "book_appointment", {"phone": AppointmentService.mask_phone(patient_phone)}, result, "failure")
            return result

    # =========================================================================
    # TOOL 3: cancel_appointment
    # =========================================================================
    @staticmethod
    def cancel_appointment(
        db: Session,
        patient_phone: str,
        appointment_id: Optional[str] = None,
        confirm_cancellation: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an existing appointment using the spoken phone number.
        Requires explicit cancellation confirmation, updates status, releases slot.
        """
        normalized_phone = AppointmentService.normalize_phone(patient_phone)
        if not AppointmentService.validate_phone(normalized_phone):
            result = {
                "success": False,
                "error": "INVALID_PHONE_NUMBER",
                "message": "Invalid phone number provided."
            }
            AppointmentService._log_tool(db, session_id, "cancel_appointment", {"phone": AppointmentService.mask_phone(patient_phone)}, result, "failure")
            return result

        # Find appointments for this caller
        appts = db.query(Appointment).filter(
            Appointment.patient_phone == normalized_phone,
            Appointment.status == "Booked"
        ).order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()

        if not appts:
            result = {
                "success": False,
                "error": "NO_APPOINTMENTS_FOUND",
                "message": f"No active appointments found for phone number ending in {normalized_phone[-4:]}."
            }
            AppointmentService._log_tool(db, session_id, "cancel_appointment", {"phone": AppointmentService.mask_phone(normalized_phone)}, result, "failure")
            return result

        # If appointment_id is not specified and caller has multiple active appointments
        target_appt = None
        if appointment_id:
            for a in appts:
                if a.appointment_id.lower() == appointment_id.lower().strip():
                    target_appt = a
                    break
            if not target_appt:
                result = {
                    "success": False,
                    "error": "APPOINTMENT_NOT_FOUND",
                    "message": f"Appointment ID '{appointment_id}' does not match any active booking for your phone number."
                }
                AppointmentService._log_tool(db, session_id, "cancel_appointment", {"appointment_id": appointment_id}, result, "failure")
                return result
        else:
            if len(appts) > 1:
                # Return multiple appointments for the caller / agent to select
                appointments_list = [
                    {
                        "appointment_id": a.appointment_id,
                        "doctor_name": a.doctor.name if a.doctor else "Unknown",
                        "speciality": a.doctor.speciality if a.doctor else "",
                        "date": a.appointment_date,
                        "time": a.start_time
                    }
                    for a in appts
                ]
                result = {
                    "success": False,
                    "error": "MULTIPLE_APPOINTMENTS",
                    "requires_selection": True,
                    "message": f"You have {len(appts)} active appointments. Please specify which appointment you would like to cancel.",
                    "appointments": appointments_list
                }
                AppointmentService._log_tool(db, session_id, "cancel_appointment", {"phone": AppointmentService.mask_phone(normalized_phone)}, result, "partial")
                return result
            else:
                target_appt = appts[0]

        if not confirm_cancellation:
            result = {
                "success": False,
                "error": "CONFIRMATION_REQUIRED",
                "message": f"Please confirm if you want to cancel appointment {target_appt.appointment_id} with {target_appt.doctor.name} on {target_appt.appointment_date} at {target_appt.start_time}."
            }
            return result

        try:
            # Atomic cancellation
            target_appt.status = "Cancelled"
            target_appt.cancelled_at = datetime.datetime.utcnow()

            # Release the slot back to Available
            slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == target_appt.slot_id).first()
            if slot:
                slot.status = "Available"

            db.commit()
            db.refresh(target_appt)

            cancellation_info = {
                "success": True,
                "appointment_id": target_appt.appointment_id,
                "doctor_name": target_appt.doctor.name if target_appt.doctor else "Unknown",
                "date": target_appt.appointment_date,
                "time": target_appt.start_time,
                "status": "Cancelled",
                "message": f"Appointment {target_appt.appointment_id} with {target_appt.doctor.name} on {target_appt.appointment_date} at {target_appt.start_time} has been successfully cancelled and the slot has been released."
            }

            AppointmentService._log_tool(db, session_id, "cancel_appointment", {"appointment_id": target_appt.appointment_id}, cancellation_info, "success")

            # Broadcast live update to frontend
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(event_service.broadcast("APPOINTMENT_CANCELLED", cancellation_info))
            except Exception:
                pass

            return cancellation_info

        except Exception as e:
            db.rollback()
            result = {
                "success": False,
                "error": "DATABASE_ERROR",
                "message": f"Failed to cancel appointment due to database error: {str(e)}"
            }
            AppointmentService._log_tool(db, session_id, "cancel_appointment", {"appointment_id": target_appt.appointment_id}, result, "failure")
            return result

    @staticmethod
    def _log_tool(db: Session, session_id: Optional[str], tool_name: str, args: Any, result: Any, status: str):
        try:
            # Mask any phone numbers before logging
            clean_args = dict(args) if isinstance(args, dict) else {"raw": str(args)}
            for k, v in clean_args.items():
                if "phone" in k.lower() and isinstance(v, str):
                    clean_args[k] = AppointmentService.mask_phone(v)
            
            log = ToolExecutionLog(
                session_id=session_id or "system",
                tool_name=tool_name,
                arguments=json.dumps(clean_args, default=str),
                result=json.dumps(result, default=str),
                status=status,
                created_at=datetime.datetime.utcnow()
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
