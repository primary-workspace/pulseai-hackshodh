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
                    file_mime_type VARCHAR,
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
        else:
            # Check if file_mime_type exists
            existing_cols = [col['name'] for col in inspector.get_columns('processed_drive_files')]
            if 'file_mime_type' not in existing_cols:
                print("Adding 'file_mime_type' column to processed_drive_files...")
                conn.execute(text("ALTER TABLE processed_drive_files ADD COLUMN file_mime_type VARCHAR"))
                conn.commit()
                print("✓ Added 'file_mime_type' column")
        
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
                    error_message TEXT,
                    error_details TEXT
                )
            """))
            conn.commit()
            print("✓ Created 'ingestion_jobs' table")
        else:
            # Check if error_details column exists
            existing_cols = [col['name'] for col in inspector.get_columns('ingestion_jobs')]
            if 'error_details' not in existing_cols:
                print("Adding 'error_details' column to ingestion_jobs...")
                conn.execute(text("ALTER TABLE ingestion_jobs ADD COLUMN error_details TEXT"))
                conn.commit()
                print("✓ Added 'error_details' column")
        
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
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level INTEGER DEFAULT 1,
                    care_score_id INTEGER REFERENCES care_scores(id),
                    title VARCHAR,
                    message TEXT,
                    health_summary TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    action_taken VARCHAR
                )
            """))
            conn.commit()
            print("✓ Created 'escalations' table")
        else:
            # Check for missing columns
            existing_cols = [col['name'] for col in inspector.get_columns('escalations')]
            
            if 'title' not in existing_cols:
                print("Adding 'title' column to escalations...")
                conn.execute(text("ALTER TABLE escalations ADD COLUMN title VARCHAR"))
                conn.commit()
            
            if 'care_score_id' not in existing_cols:
                print("Adding 'care_score_id' column to escalations...")
                conn.execute(text("ALTER TABLE escalations ADD COLUMN care_score_id INTEGER"))
                conn.commit()
            
            if 'health_summary' not in existing_cols:
                print("Adding 'health_summary' column to escalations...")
                conn.execute(text("ALTER TABLE escalations ADD COLUMN health_summary TEXT"))
                conn.commit()
            
            # Fix acknowledged column type (BOOLEAN -> INTEGER)
            # PostgreSQL doesn't have a simple way to check column type, so we try the alter
            try:
                print("Attempting to fix 'acknowledged' column type to INTEGER...")
                conn.execute(text("""
                    ALTER TABLE escalations 
                    ALTER COLUMN acknowledged TYPE INTEGER USING CASE WHEN acknowledged THEN 1 ELSE 0 END
                """))
                conn.commit()
                print("✓ Fixed 'acknowledged' column type")
            except Exception as e:
                # Column might already be INTEGER, which is fine
                conn.rollback()
                print(f"Note: acknowledged column type unchanged (may already be correct): {e}")
        
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
        else:
            # Add new columns to existing health_data table
            existing_cols = [col['name'] for col in inspector.get_columns('health_data')]
            
            new_columns = [
                ('steps', 'INTEGER'),
                ('distance', 'FLOAT'),
                ('calories_active', 'FLOAT'),
                ('calories_total', 'FLOAT'),
                ('spo2', 'FLOAT'),
                ('temperature', 'FLOAT'),
                ('weight', 'FLOAT')
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    print(f"Adding '{col_name}' column to health_data...")
                    conn.execute(text(f"ALTER TABLE health_data ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✓ Added '{col_name}' column")
        
        # ============================================
        # Multi-Role Support Tables
        # ============================================
        
        # Add role columns to users table
        if 'users' in existing_tables:
            existing_columns = [col['name'] for col in inspector.get_columns('users')]
            
            role_columns = [
                ('role', "VARCHAR DEFAULT 'patient'"),
                ('role_verified', 'BOOLEAN DEFAULT FALSE'),
                ('phone', 'VARCHAR')
            ]
            
            for col_name, col_type in role_columns:
                if col_name not in existing_columns:
                    print(f"Adding '{col_name}' column to users...")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✓ Added '{col_name}' column")
        
        # Doctor Profiles table
        if 'doctor_profiles' not in existing_tables:
            print("Creating 'doctor_profiles' table...")
            conn.execute(text("""
                CREATE TABLE doctor_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                    full_name VARCHAR NOT NULL,
                    specialization VARCHAR NOT NULL,
                    qualification VARCHAR,
                    hospital_name VARCHAR,
                    hospital_address TEXT,
                    city VARCHAR,
                    state VARCHAR,
                    country VARCHAR DEFAULT 'India',
                    emergency_contact VARCHAR,
                    consultation_hours VARCHAR,
                    license_number VARCHAR,
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ Created 'doctor_profiles' table")
        
        # Caretaker Profiles table
        if 'caretaker_profiles' not in existing_tables:
            print("Creating 'caretaker_profiles' table...")
            conn.execute(text("""
                CREATE TABLE caretaker_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                    full_name VARCHAR NOT NULL,
                    relationship_type VARCHAR,
                    phone_number VARCHAR,
                    notification_preference VARCHAR DEFAULT 'all',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ Created 'caretaker_profiles' table")
        
        # Patient-Doctor relationships table
        if 'patient_doctors' not in existing_tables:
            print("Creating 'patient_doctors' table...")
            conn.execute(text("""
                CREATE TABLE patient_doctors (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER NOT NULL REFERENCES users(id),
                    doctor_id INTEGER NOT NULL REFERENCES users(id),
                    status VARCHAR DEFAULT 'pending',
                    requested_by VARCHAR,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP,
                    patient_notes VARCHAR,
                    doctor_notes VARCHAR,
                    UNIQUE(patient_id, doctor_id)
                )
            """))
            conn.commit()
            print("✓ Created 'patient_doctors' table")
        
        # Patient-Caretaker relationships table
        if 'patient_caretakers' not in existing_tables:
            print("Creating 'patient_caretakers' table...")
            conn.execute(text("""
                CREATE TABLE patient_caretakers (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER NOT NULL REFERENCES users(id),
                    caretaker_id INTEGER NOT NULL REFERENCES users(id),
                    status VARCHAR DEFAULT 'pending',
                    access_level VARCHAR DEFAULT 'read',
                    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP,
                    invitation_code VARCHAR,
                    UNIQUE(patient_id, caretaker_id)
                )
            """))
            conn.commit()
            print("✓ Created 'patient_caretakers' table")
        
        # Notifications table
        if 'notifications' not in existing_tables:
            print("Creating 'notifications' table...")
            conn.execute(text("""
                CREATE TABLE notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    notification_type VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    message TEXT,
                    related_user_id INTEGER REFERENCES users(id),
                    related_care_score_id INTEGER,
                    is_read BOOLEAN DEFAULT FALSE,
                    is_dismissed BOOLEAN DEFAULT FALSE,
                    priority VARCHAR DEFAULT 'normal',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ Created 'notifications' table")
    
    print("\n✓ Database migration completed successfully!")

if __name__ == "__main__":
    run_migration()
