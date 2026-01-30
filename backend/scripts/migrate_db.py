"""
Database Migration Script for Pulse AI
Adds missing columns to existing tables and creates new tables
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_URL, Base
from app.models import *  # Import all models to register them

def run_migration():
    """Run database migrations to sync schema with models"""
    
    print(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    inspector = inspect(engine)
    
    # Get existing tables
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")
    
    with engine.connect() as conn:
        # ============================================
        # Users table migrations
        # ============================================
        if 'users' in existing_tables:
            existing_columns = [col['name'] for col in inspector.get_columns('users')]
            print(f"Users table columns: {existing_columns}")
            
            # Add missing columns
            if 'name' not in existing_columns:
                print("Adding 'name' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR DEFAULT 'Unknown'"))
                conn.commit()
                print("✓ Added 'name' column")
            
            if 'age' not in existing_columns:
                print("Adding 'age' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN age INTEGER"))
                conn.commit()
                print("✓ Added 'age' column")
            
            if 'gender' not in existing_columns:
                print("Adding 'gender' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR"))
                conn.commit()
                print("✓ Added 'gender' column")
            
            if 'is_active' not in existing_columns:
                print("Adding 'is_active' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                conn.commit()
                print("✓ Added 'is_active' column")
            
            # Baseline columns
            baseline_columns = [
                'baseline_heart_rate', 'baseline_hrv', 'baseline_sleep_hours',
                'baseline_activity_level', 'baseline_breathing_rate',
                'baseline_bp_systolic', 'baseline_bp_diastolic', 'baseline_blood_sugar'
            ]
            for col in baseline_columns:
                if col not in existing_columns:
                    print(f"Adding '{col}' column to users table...")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} FLOAT"))
                    conn.commit()
                    print(f"✓ Added '{col}' column")
        
        # ============================================
        # Create new tables if they don't exist
        # ============================================
        
        # Google OAuth Tokens table
        if 'google_oauth_tokens' not in existing_tables:
            print("Creating 'google_oauth_tokens' table...")
            conn.execute(text("""
                CREATE TABLE google_oauth_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_type VARCHAR DEFAULT 'Bearer',
                    expires_at TIMESTAMP,
                    scopes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ Created 'google_oauth_tokens' table")
        
        # Processed Drive Files table
        if 'processed_drive_files' not in existing_tables:
            print("Creating 'processed_drive_files' table...")
            conn.execute(text("""
                CREATE TABLE processed_drive_files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    drive_file_id VARCHAR NOT NULL,
                    file_name VARCHAR,
                    file_size BIGINT,
                    md5_checksum VARCHAR,
                    status VARCHAR DEFAULT 'pending',
                    records_imported INTEGER DEFAULT 0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    UNIQUE(user_id, drive_file_id)
                )
            """))
            conn.commit()
            print("✓ Created 'processed_drive_files' table")
        
        # Ingestion Jobs table
        if 'ingestion_jobs' not in existing_tables:
            print("Creating 'ingestion_jobs' table...")
            conn.execute(text("""
                CREATE TABLE ingestion_jobs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    job_type VARCHAR DEFAULT 'drive_sync',
                    status VARCHAR DEFAULT 'pending',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    files_found INTEGER DEFAULT 0,
                    files_processed INTEGER DEFAULT 0,
                    records_imported INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """))
            conn.commit()
            print("✓ Created 'ingestion_jobs' table")
        
        # API Keys table
        if 'api_keys' not in existing_tables:
            print("Creating 'api_keys' table...")
            conn.execute(text("""
                CREATE TABLE api_keys (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    key_hash VARCHAR NOT NULL UNIQUE,
                    name VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    revoked BOOLEAN DEFAULT FALSE
                )
            """))
            conn.commit()
            print("✓ Created 'api_keys' table")
        
        # Device Registrations table
        if 'device_registrations' not in existing_tables:
            print("Creating 'device_registrations' table...")
            conn.execute(text("""
                CREATE TABLE device_registrations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    device_id VARCHAR NOT NULL,
                    device_type VARCHAR,
                    device_name VARCHAR,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sync_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    UNIQUE(user_id, device_id)
                )
            """))
            conn.commit()
            print("✓ Created 'device_registrations' table")
        
        # Care Scores table
        if 'care_scores' not in existing_tables:
            print("Creating 'care_scores' table...")
            conn.execute(text("""
                CREATE TABLE care_scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    care_score INTEGER NOT NULL,
                    status VARCHAR,
                    severity_score FLOAT DEFAULT 0,
                    persistence_score FLOAT DEFAULT 0,
                    cross_signal_score FLOAT DEFAULT 0,
                    manual_modifier_score FLOAT DEFAULT 0,
                    drift_score FLOAT DEFAULT 0,
                    confidence_score FLOAT DEFAULT 0,
                    stability_score FLOAT DEFAULT 0,
                    explanation TEXT
                )
            """))
            conn.commit()
            print("✓ Created 'care_scores' table")
        
        # Escalations table
        if 'escalations' not in existing_tables:
            print("Creating 'escalations' table...")
            conn.execute(text("""
                CREATE TABLE escalations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    level INTEGER NOT NULL,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at TIMESTAMP,
                    action_taken VARCHAR
                )
            """))
            conn.commit()
            print("✓ Created 'escalations' table")
        
        # Health Data table
        if 'health_data' not in existing_tables:
            print("Creating 'health_data' table...")
            conn.execute(text("""
                CREATE TABLE health_data (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    timestamp TIMESTAMP NOT NULL,
                    source VARCHAR,
                    heart_rate FLOAT,
                    hrv FLOAT,
                    sleep_duration FLOAT,
                    sleep_quality FLOAT,
                    activity_level FLOAT,
                    steps INTEGER,
                    breathing_rate FLOAT,
                    bp_systolic FLOAT,
                    bp_diastolic FLOAT,
                    blood_sugar FLOAT,
                    symptoms TEXT,
                    is_anomaly BOOLEAN DEFAULT FALSE,
                    anomaly_score FLOAT
                )
            """))
            conn.commit()
            print("✓ Created 'health_data' table")
    
    print("\n✓ Database migration completed successfully!")

if __name__ == "__main__":
    run_migration()
