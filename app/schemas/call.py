# app/schemas/call.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.call import CallStatus, CallDecision

class CallBase(BaseModel):
    phone_number: str
    duration: float
    status: CallStatus
    decision: Optional[CallDecision] = None
    notes: Optional[str] = None
    client_id: Optional[int] = None

class CallCreate(CallBase):
    commercial_id: int

class CallUpdate(BaseModel):
    decision: Optional[CallDecision] = None
    notes: Optional[str] = None

class CommercialBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True

class CallResponse(CallBase):
    id: int
    commercial_id: int
    commercial: CommercialBase
    call_date: datetime

    class Config:
        from_attributes = True