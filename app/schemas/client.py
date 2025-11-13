# app/schemas/client.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ClientBase(BaseModel):
    first_name: str
    last_name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone_number: str
    address: Optional[str] = None
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    commercial_id: int

class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientBase):
    id: int
    commercial_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True