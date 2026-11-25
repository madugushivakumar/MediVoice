import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

# ----------------- Doctor Schemas -----------------
class DoctorBase(BaseModel):
    name: str
    speciality: str
    qualification: str
    experience_years: int
    department: str
    consultation_duration: int = 30
    is_active: bool = True

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime

# ----------------- Slot Schemas -----------------
class SlotBase(BaseModel):
    doctor_id: int
    appointment_date: str
    start_time: str
    end_time: str
    status: str = "Available"

class SlotResponse(SlotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
    doctor_name: Optional[str] = None
    doctor_speciality: Optional[str] = None

# ----------------- Appointment Schemas -----------------
class AppointmentCreateRequest(BaseModel):
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    slot_id: Optional[int] = None
    appointment_date: Optional[str] = None
    start_time: Optional[str] = None
    patient_phone: str = Field(..., description="Confirmed 10-digit phone number")

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    appointment_id: str
    patient_phone: str
    doctor_id: int
    doctor_name: str
    doctor_speciality: str
    slot_id: int
    appointment_date: str
    start_time: str
    status: str
    created_at: datetime.datetime
    cancelled_at: Optional[datetime.datetime] = None

# ----------------- Call & Transcript Schemas -----------------
class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: str
    speaker: str
    message: str
    timestamp: datetime.datetime
    message_status: str

class CallSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: str
    started_at: datetime.datetime
    ended_at: Optional[datetime.datetime] = None
    status: str
    duration_seconds: Optional[int] = None
    messages_count: Optional[int] = 0

# ----------------- Activity Log Schemas -----------------
class ToolLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: Optional[str] = None
    tool_name: str
    arguments: Optional[str] = None
    result: Optional[str] = None
    status: str
    created_at: datetime.datetime

# ----------------- Dashboard Stats Schemas -----------------
class DashboardStatsResponse(BaseModel):
    total_doctors: int
    available_slots_count: int
    today_appointments_count: int
    active_calls_count: int
    total_appointments_count: int
    cancelled_appointments_count: int
