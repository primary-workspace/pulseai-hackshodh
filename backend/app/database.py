"""
Pulse AI - Database Configuration
Neon PostgreSQL Connection with SQLite fallback for local development
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Track if we're using fallback
_using_fallback = False
_engine = None
_SessionLocal = None

def _create_engine_with_fallback():
    """Create database engine with fallback to SQLite if remote DB unavailable"""
    global _using_fallback, _engine, _SessionLocal
    
    database_url = DATABASE_URL
    
    # If no DATABASE_URL set, use SQLite
    if not database_url:
        logger.warning("No DATABASE_URL set, using SQLite fallback")
        database_url = "sqlite:///./pulseai_local.db"
        _using_fallback = True
    
    # Try to connect to the configured database
    try:
        if "neon.tech" in database_url:
            _engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"sslmode": "require"}
            )
        elif database_url.startswith("sqlite"):
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False}
            )
            _using_fallback = True
        else:
            _engine = create_engine(database_url, pool_pre_ping=True)
        
        # Test connection
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        if not _using_fallback:
            logger.info("Successfully connected to remote database")
        
    except OperationalError as e:
        logger.warning(f"Failed to connect to remote database: {e}")
        logger.info("Falling back to local SQLite database")
        
        # Fallback to SQLite
        database_url = "sqlite:///./pulseai_local.db"
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False}
        )
        _using_fallback = True
    
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        # Still try SQLite as last resort
        database_url = "sqlite:///./pulseai_local.db"
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False}
        )
        _using_fallback = True
    
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

# Initialize engine
engine = _create_engine_with_fallback()
SessionLocal = _SessionLocal

Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import all models to register them with Base
    from app.models import (
        user, health_data, care_score, drive_ingestion,
        doctor_profile, caretaker_profile, patient_doctor,
        patient_caretaker, notification
    )
    
    try:
        Base.metadata.create_all(bind=engine)
        if _using_fallback:
            logger.info("Database tables created using SQLite fallback")
        else:
            logger.info("Database tables created/verified on remote database")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def is_using_fallback() -> bool:
    """Check if we're using the SQLite fallback database"""
    return _using_fallback


def get_database_info() -> dict:
    """Get information about the current database connection"""
    return {
        "using_fallback": _using_fallback,
        "database_type": "sqlite" if _using_fallback else "postgresql",
        "connection_status": "connected"
    }
