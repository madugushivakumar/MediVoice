from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Doctor

class DoctorService:
    @staticmethod
    def get_all_doctors(db: Session, speciality: Optional[str] = None, is_active: bool = True) -> List[Doctor]:
        query = db.query(Doctor).filter(Doctor.is_active == is_active)
        if speciality:
            query = query.filter(Doctor.speciality.ilike(f"%{speciality.strip()}%"))
        return query.all()

    @staticmethod
    def get_doctor_by_id(db: Session, doctor_id: int) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.id == doctor_id).first()

    @staticmethod
    def get_doctor_by_name(db: Session, doctor_name: str) -> Optional[Doctor]:
        clean_name = doctor_name.lower().replace("dr.", "").replace("dr", "").strip()
        doctors = db.query(Doctor).all()
        for doc in doctors:
            doc_clean = doc.name.lower().replace("dr.", "").replace("dr", "").strip()
            if clean_name in doc_clean or doc_clean in clean_name:
                return doc
        return None

    @staticmethod
    def get_all_specialities(db: Session) -> List[str]:
        records = db.query(Doctor.speciality).distinct().all()
        return [r[0] for r in records if r[0]]
