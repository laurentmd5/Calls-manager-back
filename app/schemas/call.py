# app/schemas/call.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ..models.call import CallStatus, CallDecision


class CallBase(BaseModel):
    phone_number: str = Field(
        ...,
        example="+221771234567",
        description="Numéro de téléphone du client appelé"
    )
    duration: float = Field(
        ...,
        example=180.5,
        description="Durée de l'appel en secondes"
    )
    status: CallStatus = Field(
        ...,
        example=CallStatus.ANSWERED,
        description="Statut de l'appel (answered, missed, rejected, no_answer)"
    )
    decision: Optional[CallDecision] = Field(
        default=None,
        example=CallDecision.CALL_BACK,
        description="Décision prise après l'appel (interested, call_back, not_interested, wrong_number, no_answer)"
    )
    notes: Optional[str] = Field(
        default=None,
        example="Client intéressé, rappel prévu lundi",
        description="Notes additionnelles du commercial"
    )
    client_id: Optional[int] = Field(
        default=None,
        example=42,
        description="ID du client de la base de données (optionnel)"
    )


class CallCreate(CallBase):
    commercial_id: int = Field(
        ...,
        example=1,
        description="ID du commercial qui gère cet appel"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+221771234567",
                "duration": 180.5,
                "status": "answered",
                "decision": "call_back",
                "notes": "Client très intéressé",
                "client_id": 42,
                "commercial_id": 1
            }
        }


class CallUpdate(BaseModel):
    decision: Optional[CallDecision] = Field(
        default=None,
        example=CallDecision.CALL_BACK,
        description="Mise à jour de la décision"
    )
    notes: Optional[str] = Field(
        default=None,
        example="Rappel prévu lundi 10h",
        description="Mise à jour des notes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision": "call_back",
                "notes": "Rappel prévu lundi 10h"
            }
        }


# app/schemas/call.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ..models.call import CallStatus, CallDecision


class CallBase(BaseModel):
    phone_number: str = Field(
        ...,
        example="+221771234567",
        description="Numéro de téléphone du client appelé"
    )
    duration: float = Field(
        ...,
        example=180.5,
        description="Durée de l'appel en secondes"
    )
    status: CallStatus = Field(
        ...,
        example=CallStatus.ANSWERED,
        description="Statut de l'appel (answered, missed, rejected, no_answer)"
    )
    decision: Optional[CallDecision] = Field(
        default=None,
        example=CallDecision.CALL_BACK,
        description="Décision prise après l'appel (interested, call_back, not_interested, wrong_number, no_answer)"
    )
    notes: Optional[str] = Field(
        default=None,
        example="Client intéressé, rappel prévu lundi",
        description="Notes additionnelles du commercial"
    )
    client_id: Optional[int] = Field(
        default=None,
        example=42,
        description="ID du client de la base de données (optionnel)"
    )


class CallCreate(CallBase):
    commercial_id: int = Field(
        ...,
        example=1,
        description="ID du commercial qui gère cet appel"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+221771234567",
                "duration": 180.5,
                "status": "answered",
                "decision": "call_back",
                "notes": "Client très intéressé",
                "client_id": 42,
                "commercial_id": 1
            }
        }


class CallUpdate(BaseModel):
    decision: Optional[CallDecision] = Field(
        default=None,
        example=CallDecision.CALL_BACK,
        description="Mise à jour de la décision"
    )
    notes: Optional[str] = Field(
        default=None,
        example="Rappel prévu lundi 10h",
        description="Mise à jour des notes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision": "call_back",
                "notes": "Rappel prévu lundi 10h"
            }
        }


class CommercialBase(BaseModel):
    id: int = Field(example=1, description="ID du commercial")
    first_name: str = Field(example="Jean", description="Prénom")
    last_name: str = Field(example="Dupont", description="Nom de famille")
    email: str = Field(example="jean.dupont@netsyscall.com", description="Adresse email")

    class Config:
        from_attributes = True


class CallResponse(CallBase):
    id: int = Field(example=100, description="ID unique de l'appel")
    commercial_id: int = Field(example=1, description="ID du commercial")
    commercial: CommercialBase = Field(description="Infos détaillées du commercial")
    call_date: datetime = Field(
        example="2026-03-25T14:30:00Z",
        description="Date et heure de l'appel (ISO 8601)"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 100,
                "phone_number": "+221771234567",
                "duration": 180.5,
                "status": "answered",
                "decision": "call_back",
                "notes": "Client très intéressé",
                "client_id": 42,
                "commercial_id": 1,
                "commercial": {
                    "id": 1,
                    "first_name": "Jean",
                    "last_name": "Dupont",
                    "email": "jean.dupont@netsyscall.com"
                },
                "call_date": "2026-03-25T14:30:00Z"
            }
        }
