from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.schemas import DoctorResponse
from app.services.doctor_service import DoctorService

router = APIRouter(tags=["Doctors"])

@router.get("/doctors", response_model=List[DoctorResponse])
def get_doctors(
    speciality: Optional[str] = Query(None, description="Filter by doctor speciality"),
    db: Session = Depends(get_db)
):
    doctors = DoctorService.get_all_doctors(db, speciality=speciality)
    return doctors

@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = DoctorService.get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.get("/specialities", response_model=List[str])
def get_specialities(db: Session = Depends(get_db)):
    return DoctorService.get_all_specialities(db)
