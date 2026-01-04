import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application settings
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # Seedr client settings
    SEEDR_TIMEOUT: float = 30.0
    SEEDR_PROXY: Optional[str] = None
    
    # Token storage
    TOKEN_STORAGE_PATH: str = "tokens.json"
    
    # Auth settings
    DEFAULT_USERNAME: Optional[str] = None
    DEFAULT_PASSWORD: Optional[str] = None
    DEFAULT_AUTH: bool = False
    
    # VLC Media Player
    VLC_PATH: str = r"C:\Program Files\VideoLAN\VLC\vlc.exe"

    @property
    def encoded_proxy(self):
        if self.SEEDR_PROXY and not self.SEEDR_PROXY.strip():
            return None
        return self.SEEDR_PROXY or None

    class Config:

        env_file = ".env"
        case_sensitive = True

settings = Settings()
