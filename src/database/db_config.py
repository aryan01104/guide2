#!/usr/bin/env python3
"""
Database configuration and connection management
"""

import pathlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

# Database configuration
DB_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "activity.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize database and create tables"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"[DATABASE] Initialized database at {DB_PATH}")


def get_db_session():
    """Get database session"""
    return SessionLocal()
