# MediVoice — REST API Documentation

All REST API endpoints are served from the FastAPI backend at `http://localhost:8000`.

---

## 1. System Health
### `GET /api/health`
Checks backend service availability.
**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "MediVoice Backend & Voice Pipeline"
}
```

---

## 2. Doctors & Specialities
### `GET /api/doctors`
Returns list of active doctors.
- Query Parameter: `speciality` (optional string)

**Response `200 OK`**:
```json
[
  {
    "id": 1,
    "name": "Dr. Arjun Reddy",
    "speciality": "Cardiology",
    "qualification": "MBBS, MD, DM (Cardiology)",
    "experience_years": 14,
    "department": "Cardiology & Vascular Sciences",
    "consultation_duration": 30,
    "is_active": true,
    "created_at": "2026-11-25T06:00:00"
  }
]
```

### `GET /api/specialities`
Returns all distinct medical specialities available in the clinic.
**Response `200 OK`**:
```json
["Cardiology", "Dermatology", "Neurology", "Orthopedics", "Pediatrics", "General Medicine", "Gynecology", "ENT"]
```

---

## 3. Availability
### `GET /api/availability`
Queries available slots filtered by doctor, speciality, or requested date.
- Query Parameters: `doctor_name`, `speciality`, `date`, `preferred_time`

**Response `200 OK`**:
```json
{
  "success": true,
  "date": "2026-11-26",
  "doctors": [
    {
      "doctor_id": 1,
      "name": "Dr. Arjun Reddy",
      "speciality": "Cardiology",
      "slots_count": 6
    }
  ],
  "available_slots": [
    {
      "slot_id": 14,
      "doctor_id": 1,
      "doctor_name": "Dr. Arjun Reddy",
      "speciality": "Cardiology",
      "date": "2026-11-26",
      "start_time": "10:30 AM",
      "end_time": "11:00 AM"
    }
  ]
}
```

---

## 4. Appointments
### `GET /api/appointments`
Returns appointment records. Supports query filtering by `phone`, `status`, `date`, `doctor_id`.

### `POST /api/appointments`
Books an appointment directly via REST.
**Request Body**:
```json
{
  "patient_phone": "9876543210",
  "slot_id": 14
}
```

### `POST /api/appointments/{appointment_id}/cancel`
Cancels an appointment using the confirmed phone number.
**Request Body**:
```json
{
  "phone": "9876543210"
}
```

---

## 5. Dashboard & Analytics
### `GET /api/dashboard/stats`
Returns aggregated real-time counts:
- `total_doctors`
- `available_slots_count`
- `today_appointments_count`
- `active_calls_count`
- `total_appointments_count`
- `cancelled_appointments_count`

---

## 6. Calls & Activity
### `POST /api/calls/start`
Initializes a new voice session and returns a unique `session_id`.

### `POST /api/calls/{session_id}/end`
Terminates the voice session and saves call duration.

### `GET /api/calls/{session_id}/transcript`
Returns chronological conversation messages for the session.

### `GET /api/activity-logs`
Returns tool audit log entries (masked parameters and results).

---

## 7. WebSockets
- `GET /ws/events`: Broadcast channel for live dashboard refresh events (`APPOINTMENT_BOOKED`, `APPOINTMENT_CANCELLED`, `CALL_ENDED`).
- `GET /ws/call/{session_id}`: Bidirectional audio & transcript channel between browser and Pipecat voice pipeline.
