"""
Google OAuth Service for Pulse AI
Handles OAuth 2.0 flow for Google Drive access
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.drive_ingestion import GoogleOAuthToken


# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/google/callback")

# OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

# Required scopes for Drive access (read-only)
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


class GoogleOAuthService:
    """Service for handling Google OAuth 2.0 authentication"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate the Google OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect the user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen for refresh token
            "include_granted_scopes": "true"
        }
        
        if state:
            params["state"] = state
        
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(
        self, 
        code: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            code: Authorization code from Google callback
            
        Returns:
            Token response containing access_token, refresh_token, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(f"Token exchange failed: {error_data.get('error_description', error_data)}")
            
            return response.json()
    
    async def refresh_access_token(
        self, 
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh an expired access token
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New token response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(f"Token refresh failed: {error_data.get('error_description', error_data)}")
            
            return response.json()
    
    async def get_user_info(
        self, 
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get user profile info from Google
        
        Args:
            access_token: Valid access token
            
        Returns:
            User profile information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to fetch user info")
            
            return response.json()
    
    def save_oauth_token(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        scopes: Optional[list] = None
    ) -> GoogleOAuthToken:
        """
        Save or update OAuth tokens for a user
        
        Args:
            user_id: The user's ID
            access_token: Google access token
            refresh_token: Google refresh token
            expires_in: Token validity in seconds
            scopes: List of granted scopes
            
        Returns:
            GoogleOAuthToken object
        """
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Calculate expiration time
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check for existing token
        existing_token = self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.user_id == user_id
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.access_token = access_token
            if refresh_token:  # Only update if new refresh token provided
                existing_token.refresh_token = refresh_token
            existing_token.expires_at = expires_at
            existing_token.scopes = json.dumps(scopes) if scopes else None
            existing_token.updated_at = datetime.utcnow()
            self.db.commit()
            return existing_token
        
        # Create new token record
        oauth_token = GoogleOAuthToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=json.dumps(scopes) if scopes else None
        )
        
        self.db.add(oauth_token)
        self.db.commit()
        self.db.refresh(oauth_token)
        
        return oauth_token
    
    async def get_valid_access_token(self, user_id: int) -> Optional[str]:
        """
        Get a valid access token for a user, refreshing if necessary
        
        Args:
            user_id: The user's ID
            
        Returns:
            Valid access token or None if not available
        """
        token = self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.user_id == user_id
        ).first()
        
        if not token:
            return None
        
        # Check if token is expired
        if token.expires_at and token.expires_at < datetime.utcnow():
            # Try to refresh
            if token.refresh_token:
                try:
                    new_tokens = await self.refresh_access_token(token.refresh_token)
                    
                    # Update stored token
                    token.access_token = new_tokens.get("access_token")
                    if new_tokens.get("refresh_token"):
                        token.refresh_token = new_tokens.get("refresh_token")
                    if new_tokens.get("expires_in"):
                        token.expires_at = datetime.utcnow() + timedelta(
                            seconds=new_tokens.get("expires_in")
                        )
                    token.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    return token.access_token
                except ValueError:
                    return None
            return None
        
        return token.access_token
    
    def has_valid_oauth(self, user_id: int) -> bool:
        """Check if a user has valid OAuth credentials"""
        token = self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.user_id == user_id
        ).first()
        
        if not token:
            return False
        
        # Check if we have a refresh token (can always get new access token)
        if token.refresh_token:
            return True
        
        # Otherwise, check if access token is still valid
        if token.expires_at and token.expires_at < datetime.utcnow():
            return False
        
        return True
    
    async def revoke_token(self, user_id: int) -> bool:
        """
        Revoke OAuth access for a user
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if revocation was successful
        """
        token = self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.user_id == user_id
        ).first()
        
        if not token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    GOOGLE_REVOKE_URL,
                    params={"token": token.access_token}
                )
        except Exception:
            pass  # Revocation might fail if token is already invalid
        
        # Delete the token record
        self.db.delete(token)
        self.db.commit()
        
        return True
    
    async def create_or_update_user_from_google(
        self,
        google_user_info: Dict[str, Any],
        tokens: Dict[str, Any]
    ) -> Tuple[User, GoogleOAuthToken]:
        """
        Create or update a user based on Google profile info
        
        Args:
            google_user_info: User info from Google API
            tokens: OAuth tokens from Google
            
        Returns:
            Tuple of (User, GoogleOAuthToken)
        """
        email = google_user_info.get("email")
        name = google_user_info.get("name", email.split("@")[0])
        
        # Find or create user
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                name=name,
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        
        # Save OAuth tokens
        oauth_token = self.save_oauth_token(
            user_id=user.id,
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens.get("expires_in"),
            scopes=tokens.get("scope", "").split(" ") if tokens.get("scope") else None
        )
        
        return user, oauth_token
