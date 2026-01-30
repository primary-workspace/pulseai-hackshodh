"""
Drive Ingestion Models for Pulse AI
Tracks OAuth tokens and processed files for idempotency
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class GoogleOAuthToken(Base):
    """Stores Google OAuth tokens for users"""
    __tablename__ = "google_oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String, default="Bearer")
    
    # Token metadata
    expires_at = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=True)  # JSON array of scopes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", backref="google_oauth_token")


class ProcessedDriveFile(Base):
    """Tracks files that have been processed to ensure idempotency"""
    __tablename__ = "processed_drive_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Drive file identification
    drive_file_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=True)
    file_mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    
    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow)
    records_imported = Column(Integer, default=0)
    status = Column(String, default="completed")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Checksum for detecting file changes
    md5_checksum = Column(String, nullable=True)
    
    # Relationship
    user = relationship("User", backref="processed_drive_files")


class IngestionJob(Base):
    """Tracks ingestion jobs for monitoring and debugging"""
    __tablename__ = "ingestion_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Job metadata
    job_type = Column(String, default="drive_sync")  # drive_sync, manual_import
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Processing details
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    files_found = Column(Integer, default=0)
    files_processed = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)  # JSON for detailed error info
    
    # Relationship
    user = relationship("User", backref="ingestion_jobs")
