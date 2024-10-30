import os
import json
import logging
import uuid
import jwt  # Using PyJWT for token encoding/decoding
import argon2  # Argon2 for password hashing
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from KatamariSDK.KatamariDB import KatamariMVCC  # Assuming KatamariDB with MVCC is available
from KatamariSDK.KatamariKMS import KatamariKMS
from KatamariSDK.KatamariVault import KatamariVault

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KatamariIAM")


class User:
    def __init__(self, username: str, password_hash: Optional[str] = None, roles: List[str] = None,
                 certificate: Optional[str] = None, is_service_account: bool = False):
        self.username = username
        self.password_hash = password_hash
        self.certificate = certificate
        self.roles = roles if roles else []
        self.is_service_account = is_service_account
        self.api_key = None  # API key support for service accounts
        self.created_at = datetime.utcnow()


class KatamariIAM:
    """Identity and Access Management (IAM) module using KatamariMVCC with OAuth2 and JWT support."""

    def __init__(self, secret_key: str):
        self.katamari_mvcc = KatamariMVCC()  # Initialize the KatamariMVCC store
        self.kms = KatamariKMS()  # Initialize KatamariKMS for encryption
        self.vault = KatamariVault(self.kms)  # Initialize KatamariVault for secure secret storage
        self.token_expiry = timedelta(hours=1)  # Session token expiry duration
        self.api_key_expiry = timedelta(days=30)  # API key expiry duration for service accounts
        self.refresh_token_expiry = timedelta(days=7)  # Refresh token expiry
        self.secret_key = secret_key  # Secret key for signing JWT tokens
        self.password_hasher = argon2.PasswordHasher()  # Argon2 password hasher

    # Hash password and store securely using KatamariVault
    def hash_password_and_store(self, username: str, password: str) -> str:
        """Hash a password, encrypt, and store it securely in the vault."""
        password_hash = self.password_hasher.hash(password)
        self.vault.store_secret("katamari_secret_key", f"{username}_password", password_hash)
        return password_hash

    # Verify password using hashed value stored in KatamariVault
    def verify_password(self, username: str, password: str) -> bool:
        """Verify a password using the encrypted hash from KatamariVault."""
        stored_hash = self.vault.get_secret("katamari_secret_key", f"{username}_password")
        try:
            return self.password_hasher.verify(stored_hash, password)
        except argon2.exceptions.VerifyMismatchError:
            return False

    # Generate a JWT token
    def generate_jwt(self, subject: str, roles: List[str], expires_in: timedelta) -> str:
        """Generate a JWT token for a user or service account."""
        expiration = datetime.utcnow() + expires_in
        token = jwt.encode({
            "sub": subject,
            "roles": roles,
            "exp": expiration
        }, self.secret_key, algorithm="HS256")
        return token

    # Decode and validate a JWT token
    def decode_jwt(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired.")
        except jwt.InvalidTokenError:
            logger.error("Invalid token.")
        return None

    # Store token metadata for auditing or future revocation
    def store_token_metadata(self, token: str, subject: str, expires_at: datetime, token_type: str):
        """Store issued token metadata."""
        tx_id = self.katamari_mvcc.begin_transaction()
        self.katamari_mvcc.put(f"token:{token}", {
            "subject": subject,
            "expires_at": expires_at.isoformat(),
            "token_type": token_type,
        }, tx_id)
        self.katamari_mvcc.commit(tx_id)

    async def create_user(self, username: str, password: str, roles: List[str] = None):
        """Create a new user with Argon2-based password hashing."""
        tx_id = self.katamari_mvcc.begin_transaction()
        try:
            if self.katamari_mvcc.get(f"user:{username}", tx_id):
                raise ValueError("Username already exists")

            password_hash = self.hash_password_and_store(username, password)
            user = User(username, password_hash, roles)

            # Store user data without password
            self.katamari_mvcc.put(f"user:{username}", {
                "username": username,
                "roles": user.roles,
                "created_at": user.created_at.isoformat()
            }, tx_id)

            self.katamari_mvcc.commit(tx_id)
            logger.info(f"User {username} created successfully.")
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            self.katamari_mvcc.commit(tx_id)

    async def authenticate_user(self, username: str, password: str) -> dict:
        """Authenticate a user using Argon2 and return OAuth2 JWT token."""
        tx_id = self.katamari_mvcc.begin_transaction()
        try:
            user_data = self.katamari_mvcc.get(f"user:{username}", tx_id)
            if not user_data:
                raise ValueError("User not found")

            if not self.verify_password(username, password):
                raise ValueError("Invalid password")

            # Generate JWT token and refresh token
            access_token = self.generate_jwt(username, user_data["roles"], self.token_expiry)
            refresh_token = str(uuid.uuid4())  # Random UUID for refresh token

            # Store refresh token in the database
            self.katamari_mvcc.put(f"session:{refresh_token}", {
                "username": username,
                "expires_at": (datetime.utcnow() + self.refresh_token_expiry).isoformat()
            }, tx_id)

            self.katamari_mvcc.commit(tx_id)
            logger.info(f"User {username} authenticated and access token generated.")
            return {"access_token": access_token, "refresh_token": refresh_token}
        except Exception as e:
            logger.error(f"Authentication failed for {username}: {e}")
            self.katamari_mvcc.commit(tx_id)
            return {}

    async def refresh_oauth_token(self, refresh_token: str) -> Optional[dict]:
        """Refresh an OAuth2 token using the refresh token."""
        tx_id = self.katamari_mvcc.begin_transaction()
        try:
            session_data = self.katamari_mvcc.get(f"session:{refresh_token}", tx_id)
            if not session_data:
                raise ValueError("Invalid refresh token")

            expiry_time = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expiry_time:
                raise ValueError("Refresh token has expired")

            username = session_data["username"]
            user_data = self.katamari_mvcc.get(f"user:{username}", tx_id)
            if not user_data:
                raise ValueError("User not found")

            # Generate new access token
            new_access_token = self.generate_jwt(username, user_data["roles"], self.token_expiry)

            self.katamari_mvcc.commit(tx_id)
            return {"access_token": new_access_token}
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {e}")
            self.katamari_mvcc.commit(tx_id)
            return None

    def validate_jwt_token(self, token: str) -> bool:
        """Validate the JWT token."""
        decoded_payload = self.decode_jwt(token)
        if decoded_payload:
            logger.info(f"JWT token valid for user: {decoded_payload['sub']}")
            return True
        return False

    async def create_service_account(self, account_name: str, roles: List[str] = None):
        """Create a new service account with an API key."""
        tx_id = self.katamari_mvcc.begin_transaction()
        try:
            if self.katamari_mvcc.get(f"service:{account_name}", tx_id):
                raise ValueError("Service account already exists")

            api_key = str(uuid.uuid4())  # Generate API key
            service_account = User(account_name, roles=roles, is_service_account=True)
            service_account.api_key = api_key

            # Store API key securely in KatamariVault
            self.vault.store_secret("katamari_secret_key", f"{account_name}_api_key", api_key)

            self.katamari_mvcc.put(f"service:{account_name}", {
                "account_name": account_name,
                "roles": service_account.roles,
                "is_service_account": True,
                "created_at": service_account.created_at.isoformat(),
                "api_key_expiry": (datetime.utcnow() + self.api_key_expiry).isoformat()
            }, tx_id)

            self.katamari_mvcc.commit(tx_id)
            logger.info(f"Service account {account_name} created with API key.")
            return {"api_key": api_key}
        except Exception as e:
            logger.error(f"Error creating service account {account_name}: {e}")
            self.katamari_mvcc.commit(tx_id)
            return None

    async def authenticate_service_account(self, account_name: str, api_key: str) -> dict:
        """Authenticate a service account using API key and return JWT."""
        tx_id = self.katamari_mvcc.begin_transaction()
        try:
            account_data = self.katamari_mvcc.get(f"service:{account_name}", tx_id)
            if not account_data:
                raise ValueError("Service account not found")

            stored_api_key = self.vault.get_secret("katamari_secret_key", f"{account_name}_api_key")
            if api_key != stored_api_key:
                raise ValueError("Invalid API key")

            expiry_time = datetime.fromisoformat(account_data["api_key_expiry"])
            if datetime.utcnow() > expiry_time:
                raise ValueError("API key has expired")

            # Generate JWT token for service account
            jwt_token = self.generate_jwt(account_name, account_data["roles"], self.token_expiry)

            self.katamari_mvcc.commit(tx_id)
            logger.info(f"Service account {account_name} authenticated and JWT generated.")
            return {"access_token": jwt_token}
        except Exception as e:
            logger.error(f"Authentication failed for service account {account_name}: {e}")
            self.katamari_mvcc.commit(tx_id)
            return {}
