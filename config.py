import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Flask settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Seedr client settings
    SEEDR_TIMEOUT = float(os.getenv('SEEDR_TIMEOUT', 30.0))
    # Handle empty string proxy values
    proxy_value = os.getenv('SEEDR_PROXY', None)
    SEEDR_PROXY = proxy_value if proxy_value and proxy_value.strip() else None
    
    # Token storage
    TOKEN_STORAGE_PATH = os.getenv('TOKEN_STORAGE_PATH', 'tokens.json')
    
    # Swagger settings
    SWAGGER_UI_DOC_EXPANSION = 'list'
    RESTX_MASK_SWAGGER = False
    # Default authentication (Personal Use)
    DEFAULT_USERNAME = os.getenv('DEFAULT_USERNAME')
    DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD')
    DEFAULT_AUTH = os.getenv('DEFAULT_AUTH', 'False').lower() == 'true'
    
    # VLC Media Player
    VLC_PATH = os.getenv('VLC_PATH', r'C:\Program Files\VideoLAN\VLC\vlc.exe')
