# app/models/client.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .user import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(255))
    email = Column(String(255))
    phone_number = Column(String(20), nullable=False)
    address = Column(Text)
    notes = Column(Text)
    
    # Foreign Keys
    commercial_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    commercial = relationship("User", back_populates="clients")
    calls = relationship("Call", back_populates="client")