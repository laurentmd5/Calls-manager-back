# app/routes/calls.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database.connection import get_db
from ..schemas.call import CallCreate, CallResponse, CallUpdate
from ..services.call_service import (
    create_call, get_calls, get_call_by_id,
    update_call, get_commercial_calls,
    get_calls_stats, get_calls_by_period
)
from ..services.auth import get_current_user
from ..utils.exceptions import ResourceNotFound, UnauthorizedAccess
from ..models.user import UserRole, User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/calls",
    response_model=CallResponse,
    summary="Créer un nouvel appel",
    tags=["Calls"]
)
def create_new_call(
    call_data: CallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouvel appel commercial.
    
    **Règles:**
    - COMMERCIAL: peut créer uniquement pour lui-même
    - MANAGER/ADMIN: peut créer pour n'importe quel commercial
    """
    # Les commerciaux ne peuvent créer que leurs propres appels
    if current_user.role == UserRole.COMMERCIAL:
        call_data.commercial_id = current_user.id
    
    logger.info(
        f"Nouvel appel créé: commercial={call_data.commercial_id}, "
        f"phone={call_data.phone_number}, duration={call_data.duration}s"
    )
    
    return create_call(db, call_data)


@router.get(
    "/calls",
    response_model=List[CallResponse],
    summary="Lister les appels",
    tags=["Calls"]
)
def list_calls(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les appels avec filtrage selon le rôle.
    
    **Filtrage par rôle:**
    - COMMERCIAL: voit uniquement ses propres appels
    - MANAGER: voit tous les appels (comme admin)
    - ADMIN: voit tous les appels
    """
    if current_user.role == UserRole.COMMERCIAL:
        logger.debug(f"Récupération appels du commercial {current_user.id}")
        return get_commercial_calls(
            db, current_user.id, skip, limit, start_date, end_date
        )
    else:
        # MANAGER et ADMIN voient tous les appels
        logger.debug(f"Récupération tous appels pour {current_user.role} {current_user.id}")
        return get_calls(db, skip, limit, start_date, end_date)


@router.get(
    "/calls/stats",
    summary="Récupérer les statistiques d'appels",
    tags=["Calls"]
)
def get_statistics(
    period: str = "today",  # today, week, month
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les statistiques d'appels pour une période.
    
    **Filtre par rôle:**
    - COMMERCIAL: stats pour ses appels uniquement
    - MANAGER/ADMIN: stats pour tous les appels
    
    **Périodes disponibles:** today, week, month
    """
    if current_user.role == UserRole.COMMERCIAL:
        user_id = current_user.id
    else:
        # Manager et Admin voient tous les appels
        user_id = None
    
    logger.debug(f"Stats appels période={period}, user_id={user_id}")
    return get_calls_stats(db, user_id, period)


@router.get(
    "/calls/{call_id}",
    response_model=CallResponse,
    summary="Récupérer un appel spécifique",
    tags=["Calls"]
)
def get_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les infos d'un appel spécifique.
    
    **Permissions:**
    - COMMERCIAL: peut accéder à ses propres appels uniquement
    - MANAGER/ADMIN: accès à tous les appels
    """
    call = get_call_by_id(db, call_id)
    if not call:
        logger.warning(f"Appel {call_id} non trouvé")
        raise ResourceNotFound(f"Appel {call_id} non trouvé")
    
    # Vérifier les permissions (Manager et Admin ont accès à tous)
    if (current_user.role == UserRole.COMMERCIAL and 
        call.commercial_id != current_user.id):
        logger.warning(
            f"Accès refusé: commercial {current_user.id} "
            f"tente d'accéder appel {call_id} du commercial {call.commercial_id}"
        )
        raise UnauthorizedAccess("Vous n'avez pas accès à cet appel")
    
    return call


@router.put(
    "/calls/{call_id}",
    response_model=CallResponse,
    summary="Mettre à jour un appel",
    tags=["Calls"]
)
def update_call_info(
    call_id: int,
    call_data: CallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour un appel existant.
    
    **Permissions:**
    - COMMERCIAL: peut mettre à jour ses propres appels uniquement
    - MANAGER/ADMIN: peuvent mettre à jour tous les appels
    
    **Champs modifiables:**
    - decision: Décision prise (interested, call_back, not_interested, etc)
    - notes: Notes additionnelles
    """
    call = get_call_by_id(db, call_id)
    if not call:
        logger.warning(f"Appel {call_id} non trouvé")
        raise ResourceNotFound(f"Appel {call_id} non trouvé")
    
    # Vérifier les permissions (Manager et Admin ont accès à tous)
    if (current_user.role == UserRole.COMMERCIAL and 
        call.commercial_id != current_user.id):
        logger.warning(
            f"Accès refusé: commercial {current_user.id} "
            f"tente de modifier appel {call_id}"
        )
        raise UnauthorizedAccess("Vous n'avez pas accès à cet appel")
    
    logger.info(f"Mise à jour appel {call_id}: decision={call_data.decision}")
    return update_call(db, call_id, call_data)
