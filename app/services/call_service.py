# app/services/call_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from ..models.call import Call, CallStatus, CallDecision
from ..schemas.call import CallCreate, CallUpdate

def create_call(db: Session, call_data: CallCreate) -> Call:
    db_call = Call(**call_data.dict())
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

def get_calls(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Call]:
    query = db.query(Call)
    
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(Call.call_date >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(Call.call_date <= end)
    
    return query.order_by(Call.call_date.desc()).offset(skip).limit(limit).all()

def get_commercial_calls(
    db: Session,
    commercial_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Call]:
    query = db.query(Call).filter(Call.commercial_id == commercial_id)
    
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(Call.call_date >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(Call.call_date <= end)
    
    return query.order_by(Call.call_date.desc()).offset(skip).limit(limit).all()

def get_call_by_id(db: Session, call_id: int) -> Optional[Call]:
    return db.query(Call).filter(Call.id == call_id).first()

def update_call(db: Session, call_id: int, call_data: CallUpdate) -> Optional[Call]:
    call = get_call_by_id(db, call_id)
    if not call:
        return None
    
    update_data = call_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)
    
    db.commit()
    db.refresh(call)
    return call

def get_calls_by_period(
    db: Session,
    start_date: datetime,
    end_date: datetime,
    commercial_id: Optional[int] = None
) -> List[Call]:
    """Récupère les appels dans une période donnée pour un commercial spécifique ou tous les commerciaux."""
    query = db.query(Call).filter(
        Call.call_date >= start_date,
        Call.call_date <= end_date
    )
    
    if commercial_id:
        query = query.filter(Call.commercial_id == commercial_id)
    
    return query.order_by(Call.call_date.desc()).all()

def get_calls_stats(db: Session, user_id: Optional[int] = None, period: str = "today") -> dict:
    # Définir la période
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=30)
    
    # Construire la requête
    query = db.query(Call).filter(Call.call_date >= start_date)
    
    if user_id:
        query = query.filter(Call.commercial_id == user_id)
    
    calls = query.all()
    
    # Calculer les statistiques
    total_calls = len(calls)
    total_duration = sum(call.duration for call in calls)
    answered_calls = len([call for call in calls if call.status == CallStatus.ANSWERED])
    missed_calls = len([call for call in calls if call.status == CallStatus.MISSED])
    
    # Décisions
    decisions = {}
    for call in calls:
        if call.decision:
            decisions[call.decision] = decisions.get(call.decision, 0) + 1
    
    return {
        "period": period,
        "total_calls": total_calls,
        "total_duration": total_duration,
        "answered_calls": answered_calls,
        "missed_calls": missed_calls,
        "average_duration": total_duration / total_calls if total_calls > 0 else 0,
        "decisions": decisions
    }