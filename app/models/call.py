# app/models/call.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .user import Base

class CallStatus(str, enum.Enum):
    ANSWERED = "answered"
    MISSED = "missed"
    REJECTED = "rejected"
    NO_ANSWER = "no_answer"

class CallDecision(str, enum.Enum):
    INTERESTED = "interested"
    CALL_BACK = "call_back"
    NOT_INTERESTED = "not_interested"
    NO_ANSWER = "no_answer"
    WRONG_NUMBER = "wrong_number"

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False)
    duration = Column(Float, default=0.0)  # in seconds
    status = Column(Enum(CallStatus), nullable=False)
    decision = Column(Enum(CallDecision))
    notes = Column(Text)
    is_incoming = Column(Boolean, nullable=False, default=False)
    call_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    commercial_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    
    # Relations
    commercial = relationship("User", back_populates="calls")
    client = relationship("Client", back_populates="calls")
    recording = relationship("Recording", back_populates="call", uselist=False)
