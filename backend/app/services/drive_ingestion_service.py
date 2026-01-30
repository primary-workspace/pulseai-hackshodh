"""
Google Drive Ingestion Service for Pulse AI
Handles downloading and processing Health Connect export ZIP files from Google Drive

This service specifically handles the Health Connect SQLite schema with tables like:
- steps_record_table
- heart_rate_record_table + heart_rate_record_series_table
- sleep_session_record_table
- blood_pressure_record_table
- etc.
"""

import os
import io
import json
import zipfile
import sqlite3
import tempfile
import httpx
from typing import Optional, List, Dict, Any
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
    """Service for ingesting health data from Google Drive Health Connect exports"""
    
    # Expected filename patterns for Health Connect exports
    HEALTH_EXPORT_PATTERNS = [
        "Health Connect.zip",
        "health_connect_export.zip",
        "fit_export.zip",
        "Google Fit.zip"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.oauth_service = GoogleOAuthService(db)
    
    # ==========================================
    # Google Drive API Methods
    # ==========================================
    
    async def list_drive_files(
        self, 
        user_id: int,
        folder_id: Optional[str] = None,
        search_pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in user's Google Drive"""
        access_token = await self.oauth_service.get_valid_access_token(user_id)
        if not access_token:
            raise ValueError("No valid OAuth token available. Please re-authenticate.")
        
        # Build query
        query_parts = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if search_pattern:
            query_parts.append(f"name contains '{search_pattern}'")
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
        """Find Health Connect export files in user's Drive"""
        all_exports = []
        seen_ids = set()
        
        # Search for specific patterns
        for pattern in self.HEALTH_EXPORT_PATTERNS:
            try:
                search_term = pattern.replace(".zip", "").replace("_", " ")
                print(f"[FIND] Searching for pattern: '{search_term}'")
                files = await self.list_drive_files(user_id, search_pattern=search_term)
                
                for file in files:
                    file_name = file.get("name", "").lower()
                    file_id = file.get("id")
                    
                    if file_id not in seen_ids and file_name.endswith(".zip"):
                        all_exports.append(file)
                        seen_ids.add(file_id)
                        print(f"[FIND] ✓ Found: {file.get('name')}")
            except Exception as e:
                print(f"[FIND] Error searching for '{pattern}': {e}")
        
        # Also search for generic "health"
        try:
            files = await self.list_drive_files(user_id, search_pattern="health")
            for file in files:
                file_name = file.get("name", "").lower()
                file_id = file.get("id")
                if file_id not in seen_ids and file_name.endswith(".zip"):
                    all_exports.append(file)
                    seen_ids.add(file_id)
        except Exception:
            pass
        
        print(f"[FIND] Total health exports found: {len(all_exports)}")
        return all_exports
    
    async def download_file(self, user_id: int, file_id: str) -> bytes:
        """Download a file from Google Drive"""
        access_token = await self.oauth_service.get_valid_access_token(user_id)
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
    
    # ==========================================
    # ZIP and SQLite Processing
    # ==========================================
    
    def extract_sqlite_from_zip(self, zip_content: bytes) -> Optional[bytes]:
        """Extract SQLite database from ZIP file"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # List all files in ZIP
                all_files = zf.namelist()
                print(f"[EXTRACT] ZIP contains {len(all_files)} entries: {all_files}")
                
                # First priority: look for .db files specifically
                db_files = [f for f in all_files if f.endswith('.db')]
                print(f"[EXTRACT] Found .db files: {db_files}")
                
                if db_files:
                    # Prefer health_connect_export.db if exists
                    for db_file in db_files:
                        if 'health' in db_file.lower():
                            print(f"[EXTRACT] Extracting: {db_file}")
                            content = zf.read(db_file)
                            print(f"[EXTRACT] Extracted {len(content)} bytes")
                            return content
                    
                    # Otherwise use first .db file
                    print(f"[EXTRACT] Extracting first .db: {db_files[0]}")
                    content = zf.read(db_files[0])
                    print(f"[EXTRACT] Extracted {len(content)} bytes")
                    return content
                
                # Fallback: look for any SQLite file by magic bytes
                for name in all_files:
                    if not name.endswith('/'):  # Skip directories
                        try:
                            content = zf.read(name)
                            if len(content) >= 16 and content[:16] == b'SQLite format 3\x00':
                                print(f"[EXTRACT] Found SQLite by magic: {name}")
                                return content
                        except Exception:
                            continue
                
                print("[EXTRACT] No SQLite database found in ZIP")
        except Exception as e:
            import traceback
            print(f"[EXTRACT] Error: {e}")
            print(traceback.format_exc())
        
        return None
    
    def parse_sqlite_database(self, db_content: bytes, user_id: int) -> Dict[str, Any]:
        """Parse Health Connect SQLite database and extract health records"""
        result = {
            "tables_found": [],
            "records_parsed": 0,
            "health_records": [],
            "errors": []
        }
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp.write(db_content)
            tmp_path = tmp.name
        
        try:
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            result["tables_found"] = tables
            print(f"[PARSE] Found {len(tables)} tables")
            
            all_records = []
            
            # Extract from each supported table
            # Steps
            if "steps_record_table" in tables:
                records = self._extract_steps(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} step records")
            
            # Heart Rate (from series table)
            if "heart_rate_record_series_table" in tables:
                records = self._extract_heart_rate(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} heart rate records")
            
            # Resting Heart Rate
            if "resting_heart_rate_record_table" in tables:
                records = self._extract_resting_heart_rate(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} resting heart rate records")
            
            # Sleep
            if "sleep_session_record_table" in tables:
                records = self._extract_sleep(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} sleep records")
            
            # Blood Pressure
            if "blood_pressure_record_table" in tables:
                records = self._extract_blood_pressure(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} blood pressure records")
            
            # Blood Glucose
            if "blood_glucose_record_table" in tables:
                records = self._extract_blood_glucose(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} blood glucose records")
            
            # Respiratory Rate
            if "respiratory_rate_record_table" in tables:
                records = self._extract_respiratory_rate(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} respiratory rate records")
            
            # HRV
            if "heart_rate_variability_rmssd_record_table" in tables:
                records = self._extract_hrv(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} HRV records")
            
            # Weight
            if "weight_record_table" in tables:
                records = self._extract_weight(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} weight records")
            
            # Distance
            if "distance_record_table" in tables:
                records = self._extract_distance(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} distance records")
            
            # Active Calories
            if "active_calories_burned_record_table" in tables:
                records = self._extract_active_calories(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} active calorie records")
            
            # Total Calories
            if "total_calories_burned_record_table" in tables:
                records = self._extract_total_calories(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} total calorie records")
            
            # SpO2 (Oxygen Saturation)
            if "oxygen_saturation_record_table" in tables:
                records = self._extract_spo2(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} SpO2 records")
            
            # Body Temperature
            if "body_temperature_record_table" in tables:
                records = self._extract_temperature(cursor, user_id)
                all_records.extend(records)
                print(f"[PARSE] Extracted {len(records)} temperature records")
            
            conn.close()
            
            result["records_parsed"] = len(all_records)
            result["health_records"] = all_records
            
        except Exception as e:
            result["errors"].append(str(e))
            print(f"[PARSE] Error: {e}")
        finally:
            os.unlink(tmp_path)
        
        return result
    
    # ==========================================
    # Health Connect Data Extractors
    # ==========================================
    
    def _extract_steps(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract step count records from steps_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT count, start_time, end_time 
                FROM steps_record_table 
                WHERE count IS NOT NULL
            """)
            
            rows = cursor.fetchall()
            print(f"[EXTRACT_STEPS] Found {len(rows)} rows in steps_record_table")
            
            for row in rows:
                count, start_time, end_time = row
                print(f"[EXTRACT_STEPS] Row: count={count}, start_time={start_time}")
                if count and count > 0:
                    timestamp = self._millis_to_datetime(start_time)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "steps": int(count),
                        "activity_level": float(count)  # Map to activity_level
                    })
        except Exception as e:
            import traceback
            print(f"[EXTRACT_STEPS] Error: {e}")
            print(traceback.format_exc())
        return records
    
    def _extract_heart_rate(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract heart rate from heart_rate_record_series_table"""
        records = []
        try:
            cursor.execute("""
                SELECT beats_per_minute, epoch_millis 
                FROM heart_rate_record_series_table 
                WHERE beats_per_minute IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                bpm, epoch_millis = row
                if bpm and bpm > 0:
                    timestamp = self._millis_to_datetime(epoch_millis)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "heart_rate": float(bpm)
                    })
        except Exception as e:
            print(f"[EXTRACT_HR] Error: {e}")
        return records
    
    def _extract_resting_heart_rate(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract resting heart rate from resting_heart_rate_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT beats_per_minute, time 
                FROM resting_heart_rate_record_table 
                WHERE beats_per_minute IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                bpm, time_val = row
                if bpm and bpm > 0:
                    timestamp = self._millis_to_datetime(time_val)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "heart_rate": float(bpm)
                    })
        except Exception as e:
            print(f"[EXTRACT_RHR] Error: {e}")
        return records
    
    def _extract_sleep(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract sleep sessions from sleep_session_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT start_time, end_time, title, notes 
                FROM sleep_session_record_table
            """)
            
            for row in cursor.fetchall():
                start_time, end_time, title, notes = row
                if start_time and end_time:
                    # Calculate duration in hours
                    duration_ms = end_time - start_time
                    duration_hours = duration_ms / (1000 * 60 * 60)
                    
                    if duration_hours > 0 and duration_hours < 24:  # Sanity check
                        timestamp = self._millis_to_datetime(start_time)
                        records.append({
                            "user_id": user_id,
                            "source": "health_connect",
                            "timestamp": timestamp,
                            "sleep_duration": round(duration_hours, 2)
                        })
        except Exception as e:
            print(f"[EXTRACT_SLEEP] Error: {e}")
        return records
    
    def _extract_blood_pressure(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract blood pressure from blood_pressure_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT systolic, diastolic, time 
                FROM blood_pressure_record_table 
                WHERE systolic IS NOT NULL OR diastolic IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                systolic, diastolic, time_val = row
                if systolic or diastolic:
                    timestamp = self._millis_to_datetime(time_val)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "bp_systolic": float(systolic) if systolic else None,
                        "bp_diastolic": float(diastolic) if diastolic else None
                    })
        except Exception as e:
            print(f"[EXTRACT_BP] Error: {e}")
        return records
    
    def _extract_blood_glucose(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract blood glucose from blood_glucose_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT level, time 
                FROM blood_glucose_record_table 
                WHERE level IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                level, time_val = row
                if level:
                    timestamp = self._millis_to_datetime(time_val)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "blood_sugar": float(level)
                    })
        except Exception as e:
            print(f"[EXTRACT_GLUCOSE] Error: {e}")
        return records
    
    def _extract_respiratory_rate(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract respiratory rate from respiratory_rate_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT rate, time 
                FROM respiratory_rate_record_table 
                WHERE rate IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                rate, time_val = row
                if rate:
                    timestamp = self._millis_to_datetime(time_val)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "breathing_rate": float(rate)
                    })
        except Exception as e:
            print(f"[EXTRACT_RESP] Error: {e}")
        return records
    
    def _extract_hrv(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract HRV from heart_rate_variability_rmssd_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT heart_rate_variability_millis, time 
                FROM heart_rate_variability_rmssd_record_table 
                WHERE heart_rate_variability_millis IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                hrv_ms, time_val = row
                if hrv_ms:
                    timestamp = self._millis_to_datetime(time_val)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "hrv": float(hrv_ms)  # HRV in milliseconds
                    })
        except Exception as e:
            print(f"[EXTRACT_HRV] Error: {e}")
        return records
    
    def _extract_weight(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract weight from weight_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT weight, time 
                FROM weight_record_table 
                WHERE weight IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                weight, time_val = row
                if weight:
                    timestamp = self._millis_to_datetime(time_val)
                    # Weight is stored in kilograms in Health Connect
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "weight": float(weight)
                    })
        except Exception as e:
            print(f"[EXTRACT_WEIGHT] Error: {e}")
        return records
    
    def _extract_distance(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract distance from distance_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT distance, start_time 
                FROM distance_record_table 
                WHERE distance IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                distance, start_time = row
                if distance and distance > 0:
                    timestamp = self._millis_to_datetime(start_time)
                    # Distance is in meters
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "distance": float(distance)
                    })
        except Exception as e:
            print(f"[EXTRACT_DISTANCE] Error: {e}")
        return records
    
    def _extract_active_calories(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract active calories from active_calories_burned_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT energy, start_time 
                FROM active_calories_burned_record_table 
                WHERE energy IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                energy, start_time = row
                if energy and energy > 0:
                    timestamp = self._millis_to_datetime(start_time)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "calories_active": float(energy)
                    })
        except Exception as e:
            print(f"[EXTRACT_ACTIVE_CALORIES] Error: {e}")
        return records
    
    def _extract_total_calories(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract total calories from total_calories_burned_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT energy, start_time 
                FROM total_calories_burned_record_table 
                WHERE energy IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                energy, start_time = row
                if energy and energy > 0:
                    timestamp = self._millis_to_datetime(start_time)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "calories_total": float(energy)
                    })
        except Exception as e:
            print(f"[EXTRACT_TOTAL_CALORIES] Error: {e}")
        return records
    
    def _extract_spo2(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract SpO2 from oxygen_saturation_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT percentage, time 
                FROM oxygen_saturation_record_table 
                WHERE percentage IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                percentage, time_val = row
                if percentage:
                    timestamp = self._millis_to_datetime(time_val)
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "spo2": float(percentage)
                    })
        except Exception as e:
            print(f"[EXTRACT_SPO2] Error: {e}")
        return records
    
    def _extract_temperature(self, cursor: sqlite3.Cursor, user_id: int) -> List[Dict]:
        """Extract body temperature from body_temperature_record_table"""
        records = []
        try:
            cursor.execute("""
                SELECT temperature, time 
                FROM body_temperature_record_table 
                WHERE temperature IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                temp, time_val = row
                if temp:
                    timestamp = self._millis_to_datetime(time_val)
                    # Temperature in Celsius
                    records.append({
                        "user_id": user_id,
                        "source": "health_connect",
                        "timestamp": timestamp,
                        "temperature": float(temp)
                    })
        except Exception as e:
            print(f"[EXTRACT_TEMPERATURE] Error: {e}")
        return records
    
    def _millis_to_datetime(self, millis: int) -> datetime:
        """Convert epoch milliseconds to datetime"""
        if millis is None:
            return datetime.utcnow()
        try:
            # Health Connect uses milliseconds
            if millis > 1e12:
                return datetime.fromtimestamp(millis / 1000)
            else:
                return datetime.fromtimestamp(millis)
        except Exception:
            return datetime.utcnow()
    
    # ==========================================
    # Database Storage
    # ==========================================
    
    def save_health_records(self, records: List[Dict]) -> int:
        """Save extracted health records to database"""
        saved_count = 0
        
        for record in records:
            try:
                # Create HealthData entry with all available fields
                health_data = HealthData(
                    user_id=record.get("user_id"),
                    timestamp=record.get("timestamp", datetime.utcnow()),
                    source=record.get("source", "health_connect"),
                    # Activity
                    steps=record.get("steps"),
                    distance=record.get("distance"),
                    calories_active=record.get("calories_active"),
                    calories_total=record.get("calories_total"),
                    activity_level=record.get("activity_level"),
                    # Vitals
                    heart_rate=record.get("heart_rate"),
                    hrv=record.get("hrv"),
                    breathing_rate=record.get("breathing_rate"),
                    spo2=record.get("spo2"),
                    temperature=record.get("temperature"),
                    # Sleep
                    sleep_duration=record.get("sleep_duration"),
                    # Blood
                    bp_systolic=record.get("bp_systolic"),
                    bp_diastolic=record.get("bp_diastolic"),
                    blood_sugar=record.get("blood_sugar"),
                    # Body
                    weight=record.get("weight")
                )
                
                self.db.add(health_data)
                saved_count += 1
                
                # Commit in batches
                if saved_count % 100 == 0:
                    self.db.commit()
                    
            except Exception as e:
                import traceback
                print(f"[SAVE] Error saving record: {e}")
                print(traceback.format_exc())
                continue
        
        # Final commit
        self.db.commit()
        print(f"[SAVE] Saved {saved_count} records to database")
        return saved_count
    
    # ==========================================
    # Idempotency and File Tracking
    # ==========================================
    
    def is_file_already_processed(
        self, 
        user_id: int, 
        drive_file_id: str, 
        md5_checksum: Optional[str] = None
    ) -> bool:
        """Check if a file has already been processed successfully"""
        query = self.db.query(ProcessedDriveFile).filter(
            ProcessedDriveFile.user_id == user_id,
            ProcessedDriveFile.drive_file_id == drive_file_id
        )
        
        existing = query.first()
        
        if existing:
            print(f"[IDEMPOTENCY] Found existing record: status={existing.status}, records={existing.records_imported}")
            
            # Only skip if completed AND actually imported records
            if existing.status == "completed" and existing.records_imported and existing.records_imported > 0:
                if md5_checksum and existing.md5_checksum == md5_checksum:
                    print(f"[IDEMPOTENCY] Skipping - same checksum, already imported {existing.records_imported} records")
                    return True
                elif not md5_checksum:
                    print(f"[IDEMPOTENCY] Skipping - no checksum, already imported {existing.records_imported} records")
                    return True
            else:
                # Delete failed/empty record to allow reprocessing
                print(f"[IDEMPOTENCY] Deleting previous failed/empty record for reprocessing")
                self.db.delete(existing)
                self.db.commit()
        
        return False
    
    # ==========================================
    # Main Processing Pipeline
    # ==========================================
    
    async def process_drive_file(
        self, 
        user_id: int, 
        file_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single Drive file (full pipeline)"""
        file_id = file_metadata.get("id")
        file_name = file_metadata.get("name")
        md5_checksum = file_metadata.get("md5Checksum")
        
        print(f"[PROCESS] Starting: {file_name}")
        
        # Idempotency check
        if self.is_file_already_processed(user_id, file_id, md5_checksum):
            print(f"[PROCESS] Skipping (already processed): {file_name}")
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
            print(f"[PROCESS] Downloading...")
            zip_content = await self.download_file(user_id, file_id)
            print(f"[PROCESS] Downloaded {len(zip_content)} bytes")
            
            # Extract SQLite database
            print(f"[PROCESS] Extracting SQLite...")
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
            
            print(f"[PROCESS] Extracted {len(db_content)} bytes")
            
            # Parse health data
            print(f"[PROCESS] Parsing database...")
            parse_result = self.parse_sqlite_database(db_content, user_id)
            
            # Save health records
            print(f"[PROCESS] Saving {len(parse_result.get('health_records', []))} records...")
            records_saved = self.save_health_records(parse_result.get("health_records", []))
            
            # Update processing record
            processed_file.status = "completed"
            processed_file.records_imported = records_saved
            self.db.commit()
            
            print(f"[PROCESS] ✓ Complete: {records_saved} records saved")
            
            return {
                "status": "completed",
                "file_id": file_id,
                "file_name": file_name,
                "tables_found": parse_result.get("tables_found", []),
                "records_parsed": parse_result.get("records_parsed", 0),
                "records_saved": records_saved
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[PROCESS] Error: {e}")
            print(error_trace)
            
            processed_file.status = "failed"
            processed_file.error_message = str(e)
            self.db.commit()
            
            return {
                "status": "failed",
                "error": str(e),
                "file_id": file_id
            }
    
    async def sync_from_drive(self, user_id: int) -> Dict[str, Any]:
        """Full sync: Find and process all health exports from Drive"""
        print(f"[SYNC] Starting sync for user {user_id}")
        
        # Create ingestion job
        try:
            job = IngestionJob(
                user_id=user_id,
                job_type="drive_sync",
                status="processing"
            )
            self.db.add(job)
            self.db.commit()
            print(f"[SYNC] Created job {job.id}")
        except Exception as e:
            print(f"[SYNC] Failed to create job: {e}")
            return {"status": "failed", "error": f"Failed to create job: {str(e)}"}
        
        try:
            # Find health export files
            print(f"[SYNC] Finding health exports...")
            export_files = await self.find_health_exports(user_id)
            print(f"[SYNC] Found {len(export_files)} export files")
            
            job.files_found = len(export_files)
            
            results = []
            total_records = 0
            
            for i, file_meta in enumerate(export_files):
                print(f"[SYNC] Processing file {i+1}/{len(export_files)}: {file_meta.get('name')}")
                
                try:
                    result = await self.process_drive_file(user_id, file_meta)
                    results.append(result)
                    
                    if result.get("status") == "completed":
                        job.files_processed += 1
                        total_records += result.get("records_saved", 0)
                except Exception as e:
                    print(f"[SYNC] Error processing {file_meta.get('name')}: {e}")
                    results.append({
                        "status": "failed",
                        "error": str(e),
                        "file_name": file_meta.get('name')
                    })
            
            job.records_imported = total_records
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            print(f"[SYNC] ✓ Completed: {len(export_files)} files, {job.files_processed} processed, {total_records} records")
            
            return {
                "job_id": job.id,
                "status": "completed",
                "files_found": job.files_found,
                "files_processed": job.files_processed,
                "records_imported": total_records,
                "details": results
            }
            
        except Exception as e:
            import traceback
            print(f"[SYNC] Failed: {e}")
            print(traceback.format_exc())
            
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "job_id": job.id,
                "status": "failed",
                "error": str(e)
            }
