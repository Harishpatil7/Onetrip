from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os

# Since we now use a single PostgreSQL instance, we use a separate schema/table
# prefix via a different env var — falls back to SQLite locally
SQLALCHEMY_DATABASE_URL_STAFF = os.getenv(
    "DATABASE_URL_STAFF",
    os.getenv(
        "DATABASE_URL",        # share the same Postgres DB if only one URL is provided
        "sqlite:///./staff.db" # local fallback only
    )
)

# Render's Postgres URLs start with "postgres://" but SQLAlchemy needs "postgresql://"
if SQLALCHEMY_DATABASE_URL_STAFF.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL_STAFF = SQLALCHEMY_DATABASE_URL_STAFF.replace("postgres://", "postgresql://", 1)

engine_staff = create_engine(SQLALCHEMY_DATABASE_URL_STAFF)

SessionLocalStaff = sessionmaker(autocommit=False, autoflush=False, bind=engine_staff)
BaseStaff = declarative_base()
