from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.performance_service import PerformanceService
from app.schemas.performance import PerformanceResponse
from app.services.auth import get_current_user
from app.utils.security import has_permission
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/performance", tags=["performance"])

@router.get("/commercials", response_model=list[dict])
async def get_all_commercials_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques de performance pour tous les commerciaux.
    
    Args:
        start_date: Date de début au format YYYY-MM-DD (optionnel)
        end_date: Date de fin au format YYYY-MM-DD (optionnel)
        
    Returns:
        Liste des statistiques de performance pour chaque commercial
    """
    # Vérifier les permissions
    if not has_permission(current_user, ["read:performance"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'accéder à ces informations."
        )
    
    # Convertir les dates
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    # Récupérer les statistiques
    return PerformanceService.get_all_commercials_performance(db, start, end)

@router.get("/commercials/{commercial_id}", response_model=PerformanceResponse)
async def get_commercial_performance(
    commercial_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques de performance pour un commercial spécifique.
    
    Args:
        commercial_id: ID du commercial (doit être un nombre)
        start_date: Date de début au format YYYY-MM-DD (optionnel)
        end_date: Date de fin au format YYYY-MM-DD (optionnel)
        
    Returns:
        Statistiques de performance détaillées pour le commercial
    """
    # Vérifier si l'ID est valide
    if commercial_id == "undefined" or not commercial_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'ID du commercial est invalide ou manquant."
        )
        
    commercial_id_int = int(commercial_id)
    
    # Vérifier les permissions
    if not has_permission(current_user, ["read:performance"]) and current_user.id != commercial_id_int:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'accéder à ces informations."
        )
    
    # Convertir les dates
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    try:
        # Récupérer les statistiques
        return PerformanceService.get_commercial_performance(db, commercial_id_int, start, end)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur est survenue lors de la récupération des statistiques: {str(e)}"
        )
@router.get("/my-performance", response_model=PerformanceResponse)
async def get_my_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques de performance de l'utilisateur connecté.
    
    Args:
        start_date: Date de début au format YYYY-MM-DD (optionnel)
        end_date: Date de fin au format YYYY-MM-DD (optionnel)
        
    Returns:
        Statistiques de performance de l'utilisateur connecté
    """
    # Vérifier que l'utilisateur est un commercial
    if current_user.role != UserRole.COMMERCIAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette fonctionnalité est réservée aux commerciaux."
        )
    
    # Convertir les dates
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    try:
        # Récupérer les statistiques
        return PerformanceService.get_commercial_performance(db, current_user.id, start, end)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur est survenue lors de la récupération de vos statistiques: {str(e)}"
        )
