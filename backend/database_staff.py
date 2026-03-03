from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os

# On Render, the persistent disk is mounted at /data
# Locally it falls back to a ./database folder
DB_DIRECTORY = os.getenv("DB_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
os.makedirs(DB_DIRECTORY, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DB_DIRECTORY, 'staff.db')}"

engine_staff = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocalStaff = sessionmaker(autocommit=False, autoflush=False, bind=engine_staff)
BaseStaff = declarative_base()
