from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database_staff import BaseStaff
import datetime

class StaffAccount(BaseStaff):
    __tablename__ = "staff_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # In a production app this would be a secure hash, not plain text
    role = Column(String, default="Admin")
    office_location = Column(String, default="Main HQ")
    password_change_required = Column(Boolean, default=False)

class AuditLog(BaseStaff):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

