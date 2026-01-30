"""
Google OAuth Routes for Pulse AI
Handles OAuth 2.0 flow for Google Drive-based health data ingestion
"""

import os
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.services.google_oauth_service import GoogleOAuthService
from app.services.drive_ingestion_service import DriveIngestionService
from app.services.auth_service import AuthService


router = APIRouter(prefix="/oauth", tags=["OAuth & Drive Ingestion"])


# ============================================
# Pydantic Models
# ============================================

class OAuthStateRequest(BaseModel):
    """Request for generating OAuth state (for frontend-initiated flow)"""
    user_id: Optional[int] = None
    redirect_url: Optional[str] = None


class DriveFileInfo(BaseModel):
    """File information from Drive"""
    id: str
    name: str
    mimeType: Optional[str] = None
    size: Optional[int] = None
    md5Checksum: Optional[str] = None


class SyncRequest(BaseModel):
    """Request to trigger Drive sync"""
    user_id: int


class ProcessFileRequest(BaseModel):
    """Request to process a specific Drive file"""
    user_id: int
    file_id: str
    file_name: Optional[str] = None


# In-memory state storage (use Redis in production)
oauth_states = {}


# ============================================
# OAuth Flow Endpoints
# ============================================

@router.get("/google/authorize")
async def start_google_oauth(
    user_id: Optional[int] = None,
    redirect_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Start the Google OAuth flow
    
    This endpoint generates an authorization URL and redirects the user to Google.
    
    Args:
        user_id: Optional user ID (if user is already registered)
        redirect_url: URL to redirect to after OAuth completion
        
    Returns:
        Redirect to Google OAuth consent screen
    """
    oauth_service = GoogleOAuthService(db)
    
    # Generate secure state token
    state = secrets.token_urlsafe(32)
    
    # Store state with metadata
    oauth_states[state] = {
        "user_id": user_id,
        "redirect_url": redirect_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
    }
    
    auth_url = oauth_service.get_authorization_url(state=state)
    
    return RedirectResponse(url=auth_url)


@router.get("/google/authorize-url")
async def get_google_oauth_url(
    user_id: Optional[int] = None,
    redirect_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get Google OAuth authorization URL without redirecting
    
    Useful for SPAs that want to handle the redirect themselves.
    
    Returns:
        Authorization URL and state token
    """
    oauth_service = GoogleOAuthService(db)
    
    # Generate secure state token
    state = secrets.token_urlsafe(32)
    
    # Store state with metadata
    oauth_states[state] = {
        "user_id": user_id,
        "redirect_url": redirect_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
    }
    
    auth_url = oauth_service.get_authorization_url(state=state)
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    
    This endpoint is called by Google after user grants permission.
    It exchanges the authorization code for tokens and creates/updates the user.
    """
    # Handle errors from Google
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    # Validate state
    state_data = oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state token")
    
    oauth_service = GoogleOAuthService(db)
    
    try:
        # Exchange code for tokens
        tokens = await oauth_service.exchange_code_for_tokens(code)
        
        # Get user info from Google
        user_info = await oauth_service.get_user_info(tokens.get("access_token"))
        
        # If user_id was provided, link to existing user
        if state_data.get("user_id"):
            user = db.query(User).filter(User.id == state_data["user_id"]).first()
            if user:
                # Save OAuth tokens for existing user
                oauth_service.save_oauth_token(
                    user_id=user.id,
                    access_token=tokens.get("access_token"),
                    refresh_token=tokens.get("refresh_token"),
                    expires_in=tokens.get("expires_in"),
                    scopes=tokens.get("scope", "").split(" ") if tokens.get("scope") else None
                )
            else:
                # Create new user from Google profile
                user, _ = await oauth_service.create_or_update_user_from_google(user_info, tokens)
        else:
            # Create or update user from Google profile
            user, _ = await oauth_service.create_or_update_user_from_google(user_info, tokens)
        
        # Generate API key for the user
        auth_service = AuthService(db)
        raw_key, api_key = auth_service.generate_api_key(
            user_id=user.id,
            name="Google OAuth Key"
        )
        
        # Redirect to frontend with success
        redirect_url = state_data.get("redirect_url", "http://localhost:3000")
        
        # Add user info to redirect URL as query params
        return RedirectResponse(
            url=f"{redirect_url}?oauth=success&user_id={user.id}&api_key={raw_key}"
        )
        
    except ValueError as e:
        redirect_url = state_data.get("redirect_url", "http://localhost:3000")
        return RedirectResponse(
            url=f"{redirect_url}?oauth=error&message={str(e)}"
        )


@router.get("/google/status/{user_id}")
async def check_oauth_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a user has valid Google OAuth credentials
    
    Returns:
        OAuth status and whether Drive sync is available
    """
    oauth_service = GoogleOAuthService(db)
    has_oauth = oauth_service.has_valid_oauth(user_id)
    
    return {
        "user_id": user_id,
        "has_valid_oauth": has_oauth,
        "drive_sync_available": has_oauth
    }


@router.delete("/google/revoke/{user_id}")
async def revoke_google_oauth(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Revoke Google OAuth access for a user
    
    This removes the stored tokens and revokes access with Google.
    """
    oauth_service = GoogleOAuthService(db)
    success = await oauth_service.revoke_token(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="No OAuth token found for user")
    
    return {
        "success": True,
        "message": "Google OAuth access revoked"
    }


@router.get("/drive/debug/{user_id}")
async def debug_drive_files(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Debug endpoint: List ALL files in user's Google Drive (no filtering)
    
    This helps diagnose why certain files might not be found.
    """
    import httpx
    import json
    from app.models.drive_ingestion import GoogleOAuthToken
    
    oauth_service = GoogleOAuthService(db)
    
    # Get stored token info for debugging
    stored_token = db.query(GoogleOAuthToken).filter(
        GoogleOAuthToken.user_id == user_id
    ).first()
    
    token_info = None
    if stored_token:
        scopes = []
        if stored_token.scopes:
            try:
                scopes = json.loads(stored_token.scopes)
            except:
                scopes = [stored_token.scopes]
        
        token_info = {
            "has_access_token": bool(stored_token.access_token),
            "has_refresh_token": bool(stored_token.refresh_token),
            "expires_at": str(stored_token.expires_at) if stored_token.expires_at else None,
            "scopes": scopes,
            "created_at": str(stored_token.created_at) if stored_token.created_at else None
        }
    
    access_token = oauth_service.get_valid_access_token(user_id)
    
    if not access_token:
        return {
            "error": "No valid OAuth token", 
            "user_id": user_id,
            "token_info": token_info,
            "fix": "Please disconnect and reconnect Google Drive to get a fresh token with Drive permissions"
        }
    
    # List all files (no query filter)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "pageSize": 100,
                    "fields": "files(id, name, mimeType, size, modifiedTime)",
                    "orderBy": "modifiedTime desc"
                }
            )
            
            if response.status_code == 403:
                error_detail = response.json()
                return {
                    "error": f"Drive API error: 403 Forbidden",
                    "detail": error_detail,
                    "token_info": token_info,
                    "diagnosis": "The OAuth token does not have Drive API permissions. This can happen if:",
                    "possible_causes": [
                        "1. Drive API is not enabled in Google Cloud Console",
                        "2. The app is in 'Testing' mode and your email is not added as a test user",
                        "3. The token was obtained before the Drive scope was added",
                        "4. The user did not grant Drive access during OAuth consent"
                    ],
                    "fix": "Please disconnect and reconnect Google Drive. During OAuth consent, make sure to grant access to 'View your Google Drive files'"
                }
            
            if response.status_code != 200:
                return {
                    "error": f"Drive API error: {response.status_code}",
                    "detail": response.json(),
                    "token_info": token_info
                }
            
            all_files = response.json().get("files", [])
            
            # Also try searching for "Health"
            response2 = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "q": "name contains 'Health'",
                    "pageSize": 50,
                    "fields": "files(id, name, mimeType, size, modifiedTime)"
                }
            )
            
            health_files = []
            if response2.status_code == 200:
                health_files = response2.json().get("files", [])
            
            # Find zip files
            zip_files = [f for f in all_files if f.get("name", "").lower().endswith(".zip")]
            
            return {
                "user_id": user_id,
                "total_files": len(all_files),
                "zip_files": zip_files,
                "zip_count": len(zip_files),
                "health_search_results": health_files,
                "all_files_sample": all_files[:20],  # First 20 files
                "token_info": token_info
            }
    except Exception as e:
        return {"error": str(e), "token_info": token_info}


# ============================================
# Drive Ingestion Endpoints
# ============================================

@router.get("/drive/files/{user_id}")
async def list_drive_files(
    user_id: int,
    search: Optional[str] = None,
    folder_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List files in user's Google Drive
    
    Args:
        user_id: User's ID
        search: Optional search pattern for filename
        folder_id: Optional folder ID to search in
        
    Returns:
        List of file metadata
    """
    drive_service = DriveIngestionService(db)
    
    try:
        files = await drive_service.list_drive_files(
            user_id=user_id,
            folder_id=folder_id,
            search_pattern=search
        )
        
        return {
            "user_id": user_id,
            "files": files,
            "count": len(files)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/drive/health-exports/{user_id}")
async def find_health_exports(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Find Health Connect export files in user's Drive
    
    Searches for common Health Connect export filename patterns.
    
    Returns:
        List of found health export files
    """
    drive_service = DriveIngestionService(db)
    
    try:
        exports = await drive_service.find_health_exports(user_id)
        
        return {
            "user_id": user_id,
            "exports": exports,
            "count": len(exports)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/drive/sync")
async def sync_from_drive(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    Sync health data from Google Drive
    
    This endpoint:
    1. Finds all health export ZIP files in user's Drive
    2. Downloads and processes each file
    3. Extracts SQLite databases
    4. Parses and normalizes health data
    5. Saves to Pulse AI database
    
    Files are processed idempotently - already processed files are skipped.
    
    Returns:
        Sync job results
    """
    drive_service = DriveIngestionService(db)
    
    try:
        result = await drive_service.sync_from_drive(request.user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/drive/process-file")
async def process_single_file(
    request: ProcessFileRequest,
    db: Session = Depends(get_db)
):
    """
    Process a specific file from Google Drive
    
    Use this when you want to process a specific file instead of auto-syncing.
    
    Returns:
        Processing result
    """
    drive_service = DriveIngestionService(db)
    
    file_metadata = {
        "id": request.file_id,
        "name": request.file_name or "Unknown"
    }
    
    try:
        result = await drive_service.process_drive_file(
            user_id=request.user_id,
            file_metadata=file_metadata
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/drive/ingestion-jobs/{user_id}")
async def list_ingestion_jobs(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List recent ingestion jobs for a user
    
    Returns:
        List of ingestion job records
    """
    from app.models.drive_ingestion import IngestionJob
    
    jobs = db.query(IngestionJob).filter(
        IngestionJob.user_id == user_id
    ).order_by(IngestionJob.started_at.desc()).limit(limit).all()
    
    return {
        "user_id": user_id,
        "jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "files_found": job.files_found,
                "files_processed": job.files_processed,
                "records_imported": job.records_imported,
                "error_message": job.error_message
            }
            for job in jobs
        ]
    }


@router.get("/drive/processed-files/{user_id}")
async def list_processed_files(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List processed Drive files for a user
    
    Useful for understanding what has been imported.
    
    Returns:
        List of processed file records
    """
    from app.models.drive_ingestion import ProcessedDriveFile
    
    files = db.query(ProcessedDriveFile).filter(
        ProcessedDriveFile.user_id == user_id
    ).order_by(ProcessedDriveFile.processed_at.desc()).limit(limit).all()
    
    return {
        "user_id": user_id,
        "files": [
            {
                "id": f.id,
                "drive_file_id": f.drive_file_id,
                "file_name": f.file_name,
                "file_size": f.file_size,
                "status": f.status,
                "records_imported": f.records_imported,
                "processed_at": f.processed_at.isoformat() if f.processed_at else None,
                "error_message": f.error_message
            }
            for f in files
        ]
    }
