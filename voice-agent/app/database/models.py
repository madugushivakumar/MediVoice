import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    speciality = Column(String(100), nullable=False, index=True)
    qualification = Column(String(150), nullable=False)
    experience_years = Column(Integer, nullable=False)
    department = Column(String(150), nullable=False)
    consultation_duration = Column(Integer, default=30)  # minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    slots = relationship("AvailabilitySlot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    appointment_date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    start_time = Column(String(20), nullable=False)                    # e.g. "10:30 AM"
    end_time = Column(String(20), nullable=False)                      # e.g. "11:00 AM"
    status = Column(String(20), default="Available", index=True)       # "Available", "Booked"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    doctor = relationship("Doctor", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "appointment_date", "start_time", name="uq_doctor_slot"),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_phone = Column(String(20), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("availability_slots.id"), nullable=False, index=True)
    appointment_date = Column(String(20), nullable=False)
    start_time = Column(String(20), nullable=False)
    status = Column(String(20), default="Booked", index=True)  # "Booked", "Cancelled", "Completed"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    doctor = relationship("Doctor", back_populates="appointments")
    slot = relationship("AvailabilitySlot", back_populates="appointment")


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="active")  # "active", "ended", "failed"

    messages = relationship("ConversationMessage", back_populates="call_session", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("call_sessions.session_id"), index=True, nullable=False)
    speaker = Column(String(20), nullable=False)  # "Caller", "AI"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    message_status = Column(String(20), default="final")  # "partial", "final"

    call_session = relationship("CallSession", back_populates="messages")


class ToolExecutionLog(Base):
    __tablename__ = "tool_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=True)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    status = Column(String(20), default="success")  # "success", "failure"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
