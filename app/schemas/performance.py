from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PerformanceStats(BaseModel):
    total_calls: int = Field(..., description="Nombre total d'appels")
    answered_calls: int = Field(..., description="Nombre d'appels répondus")
    response_rate: float = Field(..., description="Taux de réponse en pourcentage")
    average_duration: float = Field(..., description="Durée moyenne des appels en secondes")
    total_duration: float = Field(..., description="Durée totale des appels en secondes")
    rating: Optional[float] = Field(None, description="Note moyenne du commercial")

class WeeklyStats(BaseModel):
    week_start: str = Field(..., description="Date de début de la semaine (YYYY-MM-DD)")
    week_end: str = Field(..., description="Date de fin de la semaine (YYYY-MM-DD)")
    calls: int = Field(..., description="Nombre d'appels cette semaine")
    answered: int = Field(..., description="Nombre d'appels répondus cette semaine")

class MonthlyStats(BaseModel):
    month: str = Field(..., description="Mois au format YYYY-MM")
    calls: int = Field(..., description="Nombre d'appels ce mois-ci")

class PerformanceResponse(BaseModel):
    stats: PerformanceStats
    weekly_stats: List[WeeklyStats]
    monthly_stats: List[MonthlyStats]
