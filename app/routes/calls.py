# app/routes/calls.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ..database.connection import get_db
from ..schemas.call import CallCreate, CallResponse, CallUpdate
from ..services.call_service import (
    create_call, get_calls, get_call_by_id,
    update_call, get_commercial_calls,
    get_calls_stats, get_calls_by_period
)
from ..utils.security import verify_token

router = APIRouter()

def get_current_user(token: str = Depends(verify_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
    return token

@router.post("/calls", response_model=CallResponse)
def create_new_call(
    call_data: CallCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Les commerciaux ne peuvent créer que leurs propres appels
    if current_user["role"] == UserRole.COMMERCIAL:
        call_data.commercial_id = current_user["user_id"]
    
    return create_call(db, call_data)

@router.get("/calls", response_model=List[CallResponse])
def list_calls(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == UserRole.COMMERCIAL:
        return get_commercial_calls(
            db, current_user["user_id"], skip, limit, start_date, end_date
        )
    else:
        return get_calls(db, skip, limit, start_date, end_date)

@router.get("/calls/stats")
def get_statistics(
    period: str = "today",  # today, week, month
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == UserRole.COMMERCIAL:
        user_id = current_user["user_id"]
    else:
        user_id = None
    
    return get_calls_stats(db, user_id, period)

@router.get("/calls/{call_id}", response_model=CallResponse)
def get_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Appel non trouvé")
    
    # Vérifier que le commercial peut accéder à cet appel
    if (current_user["role"] == UserRole.COMMERCIAL and 
        call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return call

@router.put("/calls/{call_id}", response_model=CallResponse)
def update_call_info(
    call_id: int,
    call_data: CallUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Appel non trouvé")
    
    # Vérifier les permissions
    if (current_user["role"] == UserRole.COMMERCIAL and 
        call.commercial_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return update_call(db, call_id, call_data)