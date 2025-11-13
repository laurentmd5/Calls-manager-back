# app/models/recording.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .user import Base

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    duration = Column(Float)  # in seconds
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Key
    call_id = Column(Integer, ForeignKey("calls.id"), unique=True, nullable=False)
    
    # Relations
    call = relationship("Call", back_populates="recording")