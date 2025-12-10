from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract

from app.models.user import User, UserRole
from app.models.call import Call, CallStatus
from app.schemas.performance import PerformanceStats, WeeklyStats, MonthlyStats, PerformanceResponse

class PerformanceService:
    @staticmethod
    def get_commercial_performance(
        db: Session, 
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceResponse:
        """
        Récupère les statistiques de performance pour un commercial donné.
        
        Args:
            db: Session de la base de données
            user_id: ID du commercial
            start_date: Date de début pour le filtre (optionnel)
            end_date: Date de fin pour le filtre (optionnel)
            
        Returns:
            PerformanceResponse: Objet contenant toutes les statistiques
        """
        # Vérifier si l'utilisateur existe et est un commercial
        user = db.query(User).filter(User.id == user_id, User.role == UserRole.COMMERCIAL).first()
        if not user:
            raise ValueError("Commercial non trouvé")
        
        # Définir les dates par défaut si non spécifiées
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)  # Derniers 30 jours par défaut
        
        # Filtrer les appels par date si spécifié
        query_filters = [Call.commercial_id == user_id]
        if start_date:
            query_filters.append(Call.call_date >= start_date)
        if end_date:
            query_filters.append(Call.call_date <= end_date)
        
        # Statistiques de base
        calls_query = db.query(Call).filter(*query_filters)
        total_calls = calls_query.count()
        
        # Appels répondus
        answered_calls = calls_query.filter(Call.status == CallStatus.ANSWERED).count()
        
        # Durée totale et moyenne
        duration_stats = calls_query.with_entities(
            func.sum(Call.duration).label("total_duration"),
            func.avg(Call.duration).label("avg_duration")
        ).filter(Call.status == CallStatus.ANSWERED).first()
        
        total_duration = duration_stats[0] or 0.0
        avg_duration = duration_stats[1] or 0.0
        
        # Taux de réponse
        response_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Note moyenne (à implémenter si vous avez un système de notation)
        rating = 4.5  # Valeur factice, à remplacer par votre logique de notation
        
        # Statistiques hebdomadaires (dernières 4 semaines)
        weekly_stats = PerformanceService._get_weekly_stats(db, user_id, start_date, end_date)
        
        # Statistiques mensuelles (6 derniers mois)
        monthly_stats = PerformanceService._get_monthly_stats(db, user_id, start_date, end_date)
        
        # Construire la réponse
        return PerformanceResponse(
            stats=PerformanceStats(
                total_calls=total_calls,
                answered_calls=answered_calls,
                response_rate=round(response_rate, 2),
                average_duration=round(avg_duration, 2),
                total_duration=round(total_duration, 2),
                rating=round(rating, 1) if rating else None
            ),
            weekly_stats=weekly_stats,
            monthly_stats=monthly_stats
        )
    
    @staticmethod
    def _get_weekly_stats(
        db: Session, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques hebdomadaires pour un commercial.
        """
        # Calculer le début de chaque semaine dans la plage de dates
        current_date = start_date
        weekly_stats = []
        
        while current_date < end_date:
            week_end = min(current_date + timedelta(weeks=1), end_date)
            
            # Compter les appels et les réponses pour cette semaine
            calls_count = db.query(func.count(Call.id)).filter(
                Call.commercial_id == user_id,
                Call.call_date >= current_date,
                Call.call_date < week_end
            ).scalar() or 0
            
            answered_count = db.query(func.count(Call.id)).filter(
                Call.commercial_id == user_id,
                Call.status == CallStatus.ANSWERED,
                Call.call_date >= current_date,
                Call.call_date < week_end
            ).scalar() or 0
            
            weekly_stats.append({
                'week_start': current_date.strftime('%Y-%m-%d'),
                'week_end': (week_end - timedelta(days=1)).strftime('%Y-%m-%d'),
                'calls': calls_count,
                'answered': answered_count
            })
            
            current_date = week_end
        
        return weekly_stats
    
    @staticmethod
    def _get_monthly_stats(
        db: Session, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques mensuelles pour un commercial.
        """
        # Requête pour regrouper les appels par mois (compatible MySQL)
        monthly_stats_query = db.query(
            func.DATE_FORMAT(Call.call_date, '%Y-%m-01').label('month'),
            func.count(Call.id).label('calls')
        ).filter(
            Call.commercial_id == user_id,
            Call.call_date >= start_date,
            Call.call_date <= end_date
        ).group_by(
            func.DATE_FORMAT(Call.call_date, '%Y-%m-01')
        ).order_by(
            func.DATE_FORMAT(Call.call_date, '%Y-%m-01')
        ).all()
        
        return [
            {
                'month': row[0],  # Déjà au format 'YYYY-MM-01'
                'calls': row[1]
            }
            for row in monthly_stats_query
        ]
    
    @staticmethod
    def get_all_commercials_performance(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques de performance pour tous les commerciaux.
        """
        # Récupérer tous les commerciaux
        commercials = db.query(User).filter(User.role == UserRole.COMMERCIAL, User.is_active == True).all()
        
        # Définir les dates par défaut si non spécifiées
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)  # Derniers 30 jours par défaut
        
        results = []
        for commercial in commercials:
            try:
                performance = PerformanceService.get_commercial_performance(
                    db=db,
                    user_id=commercial.id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                results.append({
                    'user_id': commercial.id,
                    'first_name': commercial.first_name,
                    'last_name': commercial.last_name,
                    'email': commercial.email,
                    'stats': performance.stats.dict(),
                    'weekly_stats': [s.dict() for s in performance.weekly_stats],
                    'monthly_stats': [m.dict() for m in performance.monthly_stats]
                })
            except Exception as e:
                print(f"Erreur lors du calcul des performances pour le commercial {commercial.id}: {str(e)}")
        
        return results
