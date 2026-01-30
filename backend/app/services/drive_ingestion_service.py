"""
Google Drive Ingestion Service for Pulse AI
Handles downloading and processing health export ZIP files from Google Drive
"""

import os
import io
import json
import zipfile
import sqlite3
import tempfile
import httpx
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.health_data import HealthData
from app.models.drive_ingestion import GoogleOAuthToken, ProcessedDriveFile, IngestionJob
from app.services.google_oauth_service import GoogleOAuthService


# Google Drive API endpoints
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_FILES_ENDPOINT = f"{DRIVE_API_BASE}/files"


class DriveIngestionService:
    """Service for ingesting health data from Google Drive exports"""
    
    # Expected filename patterns for Health Connect exports
    HEALTH_EXPORT_PATTERNS = [
        "Health Connect.zip",
        "health_connect_export.zip",
        "fit_export.zip",
        "Google Fit.zip"
    ]
    
    # SQLite table mappings for Health Connect data
    # Maps Google Fit/Health Connect table names to extraction methods
    HEALTH_TABLES = {
        "heart_rate": "_extract_heart_rate",
        "sleep_session": "_extract_sleep",
        "steps": "_extract_steps",
        "steps_count": "_extract_steps",
        "active_calories_burned": "_extract_calories",
        "respiratory_rate": "_extract_respiratory",
        "blood_pressure": "_extract_blood_pressure",
        "blood_glucose": "_extract_blood_glucose",
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.oauth_service = GoogleOAuthService(db)
    
    async def list_drive_files(
        self, 
        user_id: int,
        folder_id: Optional[str] = None,
        search_pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in user's Google Drive
        
        Args:
            user_id: User's ID
            folder_id: Optional folder ID to search in
            search_pattern: Optional filename pattern to search for
            
        Returns:
            List of file metadata dictionaries
        """
        access_token = self.oauth_service.get_valid_access_token(user_id)
        if not access_token:
            raise ValueError("No valid OAuth token available. Please re-authenticate.")
        
        # Build query
        query_parts = []
        
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        if search_pattern:
            query_parts.append(f"name contains '{search_pattern}'")
        
        # Only get files, not folders
        query_parts.append("mimeType != 'application/vnd.google-apps.folder'")
        query_parts.append("trashed = false")
        
        query = " and ".join(query_parts)
        
        params = {
            "q": query,
            "fields": "files(id, name, mimeType, size, md5Checksum, modifiedTime)",
            "orderBy": "modifiedTime desc",
            "pageSize": 100
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                DRIVE_FILES_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            
            if response.status_code != 200:
                error = response.json()
                raise ValueError(f"Drive API error: {error.get('error', {}).get('message', 'Unknown error')}")
            
            return response.json().get("files", [])
    
    async def find_health_exports(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Find Health Connect export files in user's Drive
        
        Args:
            user_id: User's ID
            
        Returns:
            List of health export file metadata
        """
        all_exports = []
        seen_ids = set()
        
        # First, search for specific known patterns
        for pattern in self.HEALTH_EXPORT_PATTERNS:
            try:
                # Search for the pattern without extension first
                search_term = pattern.replace(".zip", "").replace("_", " ")
                print(f"Searching Drive for pattern: '{search_term}'")
                files = await self.list_drive_files(user_id, search_pattern=search_term)
                print(f"  Found {len(files)} files matching '{search_term}'")
                
                for file in files:
                    file_name = file.get("name", "").lower()
                    file_id = file.get("id")
                    
                    # Check if it's a ZIP file and we haven't seen it
                    if file_id not in seen_ids and file_name.endswith(".zip"):
                        all_exports.append(file)
                        seen_ids.add(file_id)
                        print(f"  ✓ Added: {file.get('name')}")
            except ValueError as e:
                print(f"  Error searching for '{pattern}': {e}")
                continue
        
        # Also search for generic "health" + "zip" to catch variations
        try:
            print("Searching Drive for 'health'...")
            files = await self.list_drive_files(user_id, search_pattern="health")
            print(f"  Found {len(files)} files matching 'health'")
            
            for file in files:
                file_name = file.get("name", "").lower()
                file_id = file.get("id")
                
                if file_id not in seen_ids and file_name.endswith(".zip"):
                    all_exports.append(file)
                    seen_ids.add(file_id)
                    print(f"  ✓ Added: {file.get('name')}")
        except ValueError as e:
            print(f"  Error in health search: {e}")
        
        # Search for "fit" as well
        try:
            print("Searching Drive for 'fit'...")
            files = await self.list_drive_files(user_id, search_pattern="fit")
            print(f"  Found {len(files)} files matching 'fit'")
            
            for file in files:
                file_name = file.get("name", "").lower()
                file_id = file.get("id")
                
                if file_id not in seen_ids and file_name.endswith(".zip"):
                    all_exports.append(file)
                    seen_ids.add(file_id)
                    print(f"  ✓ Added: {file.get('name')}")
        except ValueError as e:
            print(f"  Error in fit search: {e}")
        
        # Last resort: search for all ZIP files
        try:
            print("Searching Drive for all '.zip' files...")
            files = await self.list_drive_files(user_id, search_pattern=".zip")
            print(f"  Found {len(files)} files matching '.zip'")
            
            for file in files:
                file_name = file.get("name", "").lower()
                file_id = file.get("id")
                
                # Check if filename might be health-related
                if file_id not in seen_ids and file_name.endswith(".zip"):
                    # Check for health-related keywords
                    health_keywords = ["health", "fit", "connect", "export", "data"]
                    if any(kw in file_name for kw in health_keywords):
                        all_exports.append(file)
                        seen_ids.add(file_id)
                        print(f"  ✓ Added (keyword match): {file.get('name')}")
        except ValueError as e:
            print(f"  Error in zip search: {e}")
        
        print(f"\nTotal health export files found: {len(all_exports)}")
        for f in all_exports:
            print(f"  - {f.get('name')} ({f.get('id')})")
        
        return all_exports
    
    async def download_file(
        self, 
        user_id: int, 
        file_id: str
    ) -> bytes:
        """
        Download a file from Google Drive
        
        Args:
            user_id: User's ID
            file_id: Drive file ID
            
        Returns:
            File contents as bytes
        """
        access_token = self.oauth_service.get_valid_access_token(user_id)
        if not access_token:
            raise ValueError("No valid OAuth token available")
        
        download_url = f"{DRIVE_FILES_ENDPOINT}/{file_id}?alt=media"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(
                download_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to download file: {response.status_code}")
            
            return response.content
    
    def is_file_already_processed(
        self, 
        user_id: int, 
        file_id: str, 
        md5_checksum: Optional[str] = None
    ) -> bool:
        """
        Check if a file has already been processed (idempotency check)
        
        Args:
            user_id: User's ID
            file_id: Drive file ID
            md5_checksum: Optional MD5 checksum to verify file hasn't changed
            
        Returns:
            True if file was already processed successfully
        """
        existing = self.db.query(ProcessedDriveFile).filter(
            ProcessedDriveFile.user_id == user_id,
            ProcessedDriveFile.drive_file_id == file_id,
            ProcessedDriveFile.status == "completed"
        ).first()
        
        if not existing:
            return False
        
        # If checksum provided, verify file hasn't changed
        if md5_checksum and existing.md5_checksum != md5_checksum:
            return False
        
        return True
    
    def extract_sqlite_from_zip(self, zip_content: bytes) -> Optional[bytes]:
        """
        Extract SQLite database from ZIP file
        
        Args:
            zip_content: ZIP file bytes
            
        Returns:
            SQLite database bytes or None if not found
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Look for .db files
                for name in zf.namelist():
                    if name.endswith(".db"):
                        return zf.read(name)
                
                # Look for common database names
                db_names = [
                    "health_connect_export.db",
                    "fit_data.db",
                    "health_data.db"
                ]
                for db_name in db_names:
                    if db_name in zf.namelist():
                        return zf.read(db_name)
        except zipfile.BadZipFile:
            return None
        
        return None
    
    def parse_sqlite_database(
        self, 
        db_content: bytes, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        Parse health data from SQLite database
        
        Args:
            db_content: SQLite database bytes
            user_id: User ID to associate data with
            
        Returns:
            Dictionary with parsed health records and statistics
        """
        result = {
            "records_parsed": 0,
            "tables_found": [],
            "errors": []
        }
        
        health_records = []
        
        # Write to temp file for SQLite access
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp.write(db_content)
            tmp_path = tmp.name
        
        try:
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            result["tables_found"] = tables
            
            # Process each recognized table
            for table_name in tables:
                for pattern, extractor_method in self.HEALTH_TABLES.items():
                    if pattern in table_name.lower():
                        try:
                            extractor = getattr(self, extractor_method)
                            records = extractor(cursor, table_name, user_id)
                            health_records.extend(records)
                        except Exception as e:
                            result["errors"].append(f"Error parsing {table_name}: {str(e)}")
            
            conn.close()
        finally:
            os.unlink(tmp_path)
        
        result["records_parsed"] = len(health_records)
        result["health_records"] = health_records
        
        return result
    
    def _extract_heart_rate(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract heart rate records"""
        records = []
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # Try to find heart rate value (various possible column names)
                hr_value = None
                for col in ["bpm", "value", "heart_rate", "heartRate", "beatsPerMinute"]:
                    if col in row_dict and row_dict[col] is not None:
                        hr_value = float(row_dict[col])
                        break
                
                if hr_value is None:
                    continue
                
                # Get timestamp
                timestamp = self._parse_timestamp(row_dict)
                
                records.append({
                    "user_id": user_id,
                    "source": "google_fit_export",
                    "timestamp": timestamp,
                    "heart_rate": hr_value
                })
        except Exception:
            pass
        
        return records
    
    def _extract_sleep(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract sleep records"""
        records = []
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # Try to find sleep duration
                duration = None
                for col in ["duration", "duration_millis", "durationMs", "totalSleepTime"]:
                    if col in row_dict and row_dict[col] is not None:
                        duration = float(row_dict[col])
                        # Convert milliseconds to hours if needed
                        if "millis" in col.lower() or "ms" in col.lower():
                            duration = duration / (1000 * 60 * 60)
                        break
                
                if duration is None:
                    continue
                
                # Get timestamp
                timestamp = self._parse_timestamp(row_dict)
                
                # Try to get sleep quality/stage
                quality = None
                for col in ["quality", "stage", "sleepStage", "sleepQuality"]:
                    if col in row_dict and row_dict[col] is not None:
                        quality = float(row_dict[col]) if isinstance(row_dict[col], (int, float)) else None
                        break
                
                records.append({
                    "user_id": user_id,
                    "source": "google_fit_export",
                    "timestamp": timestamp,
                    "sleep_duration": duration,
                    "sleep_quality": quality
                })
        except Exception:
            pass
        
        return records
    
    def _extract_steps(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract step count records"""
        records = []
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # Try to find step count
                steps = None
                for col in ["steps", "count", "value", "stepCount"]:
                    if col in row_dict and row_dict[col] is not None:
                        steps = float(row_dict[col])
                        break
                
                if steps is None:
                    continue
                
                # Get timestamp
                timestamp = self._parse_timestamp(row_dict)
                
                records.append({
                    "user_id": user_id,
                    "source": "google_fit_export",
                    "timestamp": timestamp,
                    "activity_level": steps  # Map steps to activity_level
                })
        except Exception:
            pass
        
        return records
    
    def _extract_calories(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract calorie records - currently just logging, not storing separately"""
        # Calories are not directly mapped in the current HealthData model
        # This could be extended in the future
        return []
    
    def _extract_respiratory(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract respiratory rate records"""
        records = []
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # Try to find respiratory rate
                resp_rate = None
                for col in ["rate", "value", "respiratoryRate", "breathsPerMinute"]:
                    if col in row_dict and row_dict[col] is not None:
                        resp_rate = float(row_dict[col])
                        break
                
                if resp_rate is None:
                    continue
                
                # Get timestamp
                timestamp = self._parse_timestamp(row_dict)
                
                records.append({
                    "user_id": user_id,
                    "source": "google_fit_export",
                    "timestamp": timestamp,
                    "breathing_rate": resp_rate
                })
        except Exception:
            pass
        
        return records
    
    def _extract_blood_pressure(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract blood pressure records"""
        records = []
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # Try to find systolic and diastolic
                systolic = None
                diastolic = None
                
                for col in ["systolic", "systolicPressure", "sys"]:
                    if col in row_dict and row_dict[col] is not None:
                        systolic = float(row_dict[col])
                        break
                
                for col in ["diastolic", "diastolicPressure", "dia"]:
                    if col in row_dict and row_dict[col] is not None:
                        diastolic = float(row_dict[col])
                        break
                
                if systolic is None and diastolic is None:
                    continue
                
                # Get timestamp
                timestamp = self._parse_timestamp(row_dict)
                
                records.append({
                    "user_id": user_id,
                    "source": "google_fit_export",
                    "timestamp": timestamp,
                    "bp_systolic": systolic,
                    "bp_diastolic": diastolic
                })
        except Exception:
            pass
        
        return records
    
    def _extract_blood_glucose(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        user_id: int
    ) -> List[Dict]:
        """Extract blood glucose records"""
        records = []
        
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                # Try to find glucose level
                glucose = None
                for col in ["level", "value", "glucose", "bloodGlucose", "mgdl"]:
                    if col in row_dict and row_dict[col] is not None:
                        glucose = float(row_dict[col])
                        break
                
                if glucose is None:
                    continue
                
                # Get timestamp
                timestamp = self._parse_timestamp(row_dict)
                
                records.append({
                    "user_id": user_id,
                    "source": "google_fit_export",
                    "timestamp": timestamp,
                    "blood_sugar": glucose
                })
        except Exception:
            pass
        
        return records
    
    def _parse_timestamp(self, row_dict: Dict) -> datetime:
        """Parse timestamp from various possible column names and formats"""
        timestamp_cols = [
            "timestamp", "time", "dateTime", "start_time", 
            "startTime", "date", "created_at", "recorded_at"
        ]
        
        for col in timestamp_cols:
            if col in row_dict and row_dict[col] is not None:
                value = row_dict[col]
                
                # Handle epoch milliseconds
                if isinstance(value, (int, float)):
                    if value > 1e12:  # Milliseconds
                        return datetime.fromtimestamp(value / 1000)
                    else:  # Seconds
                        return datetime.fromtimestamp(value)
                
                # Handle ISO format string
                if isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        try:
                            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            pass
        
        # Default to current time if no timestamp found
        return datetime.utcnow()
    
    def save_health_records(
        self, 
        health_records: List[Dict]
    ) -> int:
        """
        Save parsed health records to database
        
        Args:
            health_records: List of health record dictionaries
            
        Returns:
            Number of records saved
        """
        saved_count = 0
        
        for record in health_records:
            health_data = HealthData(
                user_id=record.get("user_id"),
                source=record.get("source", "google_fit_export"),
                timestamp=record.get("timestamp", datetime.utcnow()),
                heart_rate=record.get("heart_rate"),
                hrv=record.get("hrv"),
                sleep_duration=record.get("sleep_duration"),
                sleep_quality=record.get("sleep_quality"),
                activity_level=record.get("activity_level"),
                breathing_rate=record.get("breathing_rate"),
                bp_systolic=record.get("bp_systolic"),
                bp_diastolic=record.get("bp_diastolic"),
                blood_sugar=record.get("blood_sugar")
            )
            
            self.db.add(health_data)
            saved_count += 1
        
        self.db.commit()
        return saved_count
    
    async def process_drive_file(
        self, 
        user_id: int, 
        file_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single Drive file (full pipeline)
        
        Args:
            user_id: User's ID
            file_metadata: File metadata from Drive API
            
        Returns:
            Processing result
        """
        file_id = file_metadata.get("id")
        file_name = file_metadata.get("name")
        md5_checksum = file_metadata.get("md5Checksum")
        
        # Idempotency check
        if self.is_file_already_processed(user_id, file_id, md5_checksum):
            return {
                "status": "skipped",
                "reason": "File already processed",
                "file_id": file_id,
                "file_name": file_name
            }
        
        # Create processing record
        processed_file = ProcessedDriveFile(
            user_id=user_id,
            drive_file_id=file_id,
            file_name=file_name,
            file_mime_type=file_metadata.get("mimeType"),
            file_size=int(file_metadata.get("size", 0)) if file_metadata.get("size") else None,
            md5_checksum=md5_checksum,
            status="processing"
        )
        self.db.add(processed_file)
        self.db.commit()
        
        try:
            # Download ZIP file
            zip_content = await self.download_file(user_id, file_id)
            
            # Extract SQLite database
            db_content = self.extract_sqlite_from_zip(zip_content)
            if not db_content:
                processed_file.status = "failed"
                processed_file.error_message = "No SQLite database found in ZIP"
                self.db.commit()
                return {
                    "status": "failed",
                    "error": "No SQLite database found in ZIP",
                    "file_id": file_id
                }
            
            # Parse health data
            parse_result = self.parse_sqlite_database(db_content, user_id)
            
            # Save health records
            records_saved = self.save_health_records(parse_result.get("health_records", []))
            
            # Update processing record
            processed_file.status = "completed"
            processed_file.records_imported = records_saved
            self.db.commit()
            
            return {
                "status": "completed",
                "file_id": file_id,
                "file_name": file_name,
                "tables_found": parse_result.get("tables_found", []),
                "records_parsed": parse_result.get("records_parsed", 0),
                "records_saved": records_saved,
                "errors": parse_result.get("errors", [])
            }
            
        except Exception as e:
            processed_file.status = "failed"
            processed_file.error_message = str(e)
            self.db.commit()
            
            return {
                "status": "failed",
                "error": str(e),
                "file_id": file_id
            }
    
    async def sync_from_drive(self, user_id: int) -> Dict[str, Any]:
        """
        Full sync: Find and process all health exports from Drive
        
        Args:
            user_id: User's ID
            
        Returns:
            Sync results summary
        """
        # Create ingestion job
        job = IngestionJob(
            user_id=user_id,
            job_type="drive_sync",
            status="processing"
        )
        self.db.add(job)
        self.db.commit()
        
        try:
            # Find health export files
            export_files = await self.find_health_exports(user_id)
            job.files_found = len(export_files)
            
            results = []
            total_records = 0
            
            for file_meta in export_files:
                result = await self.process_drive_file(user_id, file_meta)
                results.append(result)
                
                if result.get("status") == "completed":
                    job.files_processed += 1
                    total_records += result.get("records_saved", 0)
            
            job.records_imported = total_records
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "job_id": job.id,
                "status": "completed",
                "files_found": job.files_found,
                "files_processed": job.files_processed,
                "records_imported": total_records,
                "details": results
            }
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "job_id": job.id,
                "status": "failed",
                "error": str(e)
            }
