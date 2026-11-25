import datetime
from typing import List, Dict, Any, Optional
from app.database.connection import SessionLocal
from app.database.models import CallSession, ConversationMessage

class ConversationState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status: str = "CONNECTING"
        self.transcript: List[Dict[str, Any]] = []
        self.spoken_phone: Optional[str] = None
        self.confirmed_phone: Optional[str] = None
        self.selected_doctor: Optional[str] = None
        self.selected_slot_id: Optional[int] = None
        self.selected_time: Optional[str] = None
        self.selected_date: Optional[str] = None
        self.booking_confirmed: bool = False
        self.cancellation_confirmed: bool = False
        self.started_at: datetime.datetime = datetime.datetime.utcnow()
        self.ended_at: Optional[datetime.datetime] = None

        # Create session in database
        self._init_session_record()

    def _init_session_record(self):
        db = SessionLocal()
        try:
            session = db.query(CallSession).filter(CallSession.session_id == self.session_id).first()
            if not session:
                session = CallSession(
                    session_id=self.session_id,
                    started_at=self.started_at,
                    status="active"
                )
                db.add(session)
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def add_message(self, speaker: str, message: str, status: str = "final"):
        now = datetime.datetime.utcnow()
        msg_obj = {
            "speaker": speaker,
            "message": message,
            "timestamp": now.isoformat(),
            "status": status
        }
        self.transcript.append(msg_obj)

        if status == "final":
            db = SessionLocal()
            try:
                record = ConversationMessage(
                    session_id=self.session_id,
                    speaker=speaker,
                    message=message,
                    timestamp=now,
                    message_status=status
                )
                db.add(record)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

    def set_status(self, new_status: str):
        self.status = new_status

    def end_call(self):
        self.status = "ENDED"
        self.ended_at = datetime.datetime.utcnow()
        db = SessionLocal()
        try:
            session = db.query(CallSession).filter(CallSession.session_id == self.session_id).first()
            if session:
                session.status = "ended"
                session.ended_at = self.ended_at
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
