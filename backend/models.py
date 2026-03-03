from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # State management for the bot
    bot_state = Column(String, default="START") 
    selected_service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    
    # Track their chosen language
    language = Column(String, default="EN")

    appointments = relationship("Appointment", back_populates="citizen")
    selected_service = relationship("Service")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    
    name_en = Column(String, unique=True, index=True) 
    required_docs_en = Column(String) 

    name_kn = Column(String, nullable=True) 
    required_docs_kn = Column(String, nullable=True) 

    appointments = relationship("Appointment", back_populates="service")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    
    token_number = Column(String, unique=True, index=True)
    status = Column(String, default="PENDING")
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

    citizen = relationship("Citizen", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
