from sqlalchemy import Column, Integer, String
from database_staff import BaseStaff

class StaffAccount(BaseStaff):
    __tablename__ = "staff_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # In a production app this would be a secure hash, not plain text
    role = Column(String, default="Admin")
    office_location = Column(String, default="Main HQ")
