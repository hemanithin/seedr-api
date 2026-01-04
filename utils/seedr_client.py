import json
import os
from threading import Lock
from typing import Optional, Dict, Any
from seedrcc import Seedr
from config import settings


class SeedrClientManager:
    """Manages Seedr client instances and token storage"""
    
    def __init__(self):
        self.clients: Dict[str, Seedr] = {}
        self.lock = Lock()
        self.token_storage_path = settings.TOKEN_STORAGE_PATH
        self._default_auth_initialized = False
    
    def _token_to_dict(self, token_data: Any) -> Dict[str, Any]:
        """Convert token data to dictionary format"""
        # If it's already a dict, return as-is
        if isinstance(token_data, dict):
            return token_data
        
        # If it's a Token object, try to convert it
        if hasattr(token_data, '__dict__'):
            return token_data.__dict__
        
        # If it has a to_dict method, use it
        if hasattr(token_data, 'to_dict'):
            return token_data.to_dict()
        
        # Fallback: try to serialize and deserialize
        try:
            return json.loads(json.dumps(token_data, default=str))
        except:
            raise ValueError(f"Cannot convert token data of type {type(token_data)} to dict")
    
    def _save_token(self, user_id: str, token_data: Any):
        """Save token data to storage"""
        try:
            # Load existing tokens
            tokens = {}
            if os.path.exists(self.token_storage_path):
                try:
                    with open(self.token_storage_path, 'r') as f:
                        tokens = json.load(f)
                except json.JSONDecodeError as json_err:
                    print(f"Warning: Corrupted token file detected ({json_err}). Resetting token storage.")
                    tokens = {}
            
            # Update with new token (convert to dict if needed)
            tokens[user_id] = self._token_to_dict(token_data)
            
            # Save back to file
            with open(self.token_storage_path, 'w') as f:
                json.dump(tokens, f, indent=2)
        except Exception as e:
            print(f"Error saving token: {e}")
    
    def _load_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load token data from storage"""
        try:
            if os.path.exists(self.token_storage_path):
                try:
                    with open(self.token_storage_path, 'r') as f:
                        tokens = json.load(f)
                        return tokens.get(user_id)
                except json.JSONDecodeError as json_err:
                    print(f"Warning: Corrupted token file detected while loading ({json_err}). Cannot load token.")
                    return None
        except Exception as e:
            print(f"Error loading token: {e}")
        return None
    
    def create_client_from_password(self, username: str, password: str) -> Seedr:
        """Create Seedr client using password authentication"""
        def on_token_refresh(token_data):
            self._save_token(username, token_data)
        
        client = Seedr.from_password(
            username=username,
            password=password,
            on_token_refresh=on_token_refresh,
            timeout=settings.SEEDR_TIMEOUT,
            proxy=settings.encoded_proxy
        )
        
        with self.lock:
            self.clients[username] = client
        
        # Save initial token
        if hasattr(client, 'token'):
            self._save_token(username, client.token)
        
        return client
    
    def create_client_from_device_code(self, device_code: str, user_id: str = 'default') -> Seedr:
        """Create Seedr client using device code authentication"""
        def on_token_refresh(token_data):
            self._save_token(user_id, token_data)
        
        client = Seedr.from_device_code(
            device_code=device_code,
            on_token_refresh=on_token_refresh,
            timeout=settings.SEEDR_TIMEOUT,
            proxy=settings.encoded_proxy
        )
        
        with self.lock:
            self.clients[user_id] = client
        
        # Save initial token
        if hasattr(client, 'token'):
            self._save_token(user_id, client.token)
        
        return client
    
    def create_client_from_refresh_token(self, refresh_token: str, user_id: str = 'default') -> Seedr:
        """Create Seedr client using refresh token"""
        def on_token_refresh(token_data):
            self._save_token(user_id, token_data)
        
        client = Seedr.from_refresh_token(
            refresh_token=refresh_token,
            on_token_refresh=on_token_refresh,
            timeout=settings.SEEDR_TIMEOUT,
            proxy=settings.encoded_proxy
        )
        
        with self.lock:
            self.clients[user_id] = client
        
        # Save initial token
        if hasattr(client, 'token'):
            self._save_token(user_id, client.token)
        
        return client
    
    def create_client_from_token(self, token: Dict[str, Any], user_id: str = 'default') -> Seedr:
        """Create Seedr client from token data"""
        def on_token_refresh(token_data):
            self._save_token(user_id, token_data)
        
        client = Seedr(
            token=token,
            on_token_refresh=on_token_refresh,
            timeout=settings.SEEDR_TIMEOUT,
            proxy=settings.encoded_proxy
        )
        
        with self.lock:
            self.clients[user_id] = client
        
        return client
    
    def get_effective_user_id(self, requested_user_id: str = 'default') -> str:
        """Get effective user_id based on DEFAULT_AUTH setting"""
        if settings.DEFAULT_AUTH:
            return 'default'
        return requested_user_id
    
    def initialize_default_auth(self) -> bool:
        """Initialize default authentication if DEFAULT_AUTH is enabled"""
        if not settings.DEFAULT_AUTH:
            return False
        
        if self._default_auth_initialized:
            return True
        
        if not settings.DEFAULT_USERNAME or not settings.DEFAULT_PASSWORD:
            print("WARNING: DEFAULT_AUTH is enabled but DEFAULT_USERNAME or DEFAULT_PASSWORD is not set")
            return False
        
        try:
            print(f"Initializing default authentication for user: {settings.DEFAULT_USERNAME}")
            self.create_client_from_password(settings.DEFAULT_USERNAME, settings.DEFAULT_PASSWORD)
            # Store as 'default' user_id
            with self.lock:
                if settings.DEFAULT_USERNAME in self.clients:
                    self.clients['default'] = self.clients[settings.DEFAULT_USERNAME]
            self._default_auth_initialized = True
            print("Default authentication initialized successfully")
            return True
        except Exception as e:
            print(f"Failed to initialize default authentication: {e}")
            return False
    
    def get_client(self, user_id: str = 'default') -> Optional[Seedr]:
        """Get existing client or create from stored token"""
        # Auto-initialize if DEFAULT_AUTH is enabled and not yet initialized
        if settings.DEFAULT_AUTH and not self._default_auth_initialized:
            self.initialize_default_auth()
        
        # Enforce default user_id if DEFAULT_AUTH is enabled
        effective_user_id = self.get_effective_user_id(user_id)
        
        with self.lock:
            if effective_user_id in self.clients:
                return self.clients[effective_user_id]
        
        # Try to load from storage
        token_data = self._load_token(effective_user_id)
        if token_data:
            return self.create_client_from_token(token_data, effective_user_id)
        
        return None
    
    def remove_client(self, user_id: str):
        """Remove client and token"""
        with self.lock:
            if user_id in self.clients:
                try:
                    self.clients[user_id].close()
                except:
                    pass
                del self.clients[user_id]
        
        # Remove from storage
        try:
            if os.path.exists(self.token_storage_path):
                try:
                    with open(self.token_storage_path, 'r') as f:
                        tokens = json.load(f)
                except json.JSONDecodeError as json_err:
                    print(f"Warning: Corrupted token file detected while removing ({json_err}). Resetting token storage.")
                    tokens = {}
                if user_id in tokens:
                    del tokens[user_id]
                    with open(self.token_storage_path, 'w') as f:
                        json.dump(tokens, f, indent=2)
        except Exception as e:
            print(f"Error removing token: {e}")


# Global client manager instance
client_manager = SeedrClientManager()
