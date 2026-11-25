from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import CallSession, ConversationMessage, ToolExecutionLog
from app.database.schemas import CallSessionResponse, MessageResponse, ToolLogResponse

router = APIRouter(tags=["Calls & Activity"])

@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "MediVoice Backend & Voice Pipeline"}

@router.get("/calls", response_model=List[CallSessionResponse])
def get_call_sessions(db: Session = Depends(get_db)):
    sessions = db.query(CallSession).order_by(CallSession.started_at.desc()).all()
    results = []
    for s in sessions:
        duration = None
        if s.ended_at and s.started_at:
            duration = int((s.ended_at - s.started_at).total_seconds())
        msg_count = db.query(ConversationMessage).filter(ConversationMessage.session_id == s.session_id).count()
        results.append(
            CallSessionResponse(
                id=s.id,
                session_id=s.session_id,
                started_at=s.started_at,
                ended_at=s.ended_at,
                status=s.status,
                duration_seconds=duration,
                messages_count=msg_count
            )
        )
    return results

@router.get("/calls/{session_id}/transcript", response_model=List[MessageResponse])
def get_session_transcript(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).order_by(ConversationMessage.timestamp.asc()).all()
    return messages

@router.get("/activity-logs", response_model=List[ToolLogResponse])
def get_activity_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(ToolExecutionLog).order_by(ToolExecutionLog.created_at.desc()).limit(limit).all()
    return logs
