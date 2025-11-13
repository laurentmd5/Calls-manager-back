# app/schemas/recording.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RecordingBase(BaseModel):
    filename: str
    file_path: str
    file_size: Optional[int] = None
    duration: Optional[float] = None

class RecordingCreate(RecordingBase):
    call_id: int

class RecordingResponse(RecordingBase):
    id: int
    call_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True