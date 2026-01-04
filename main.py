import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import auth, account, files, torrents, vlc

# Setup logging


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application services on startup"""
    if settings.DEFAULT_AUTH:
        logger.info("🔐 Default Authentication: ENABLED")
        logger.info(f"👤 Default User: {settings.DEFAULT_USERNAME}")
        
        # Proactively initialize default auth
        from utils.seedr_client import client_manager
        try:
            if client_manager.initialize_default_auth():
                logger.info("✅ Default authentication initialized successfully")
            else:
                logger.warning("⚠️ Failed to initialize default authentication")
        except Exception as e:
            logger.error(f"❌ Error initializing default authentication: {str(e)}")
    else:
        logger.info("🔓 Default Authentication: DISABLED")
    yield
    # Cleanup code can go here if needed

def create_app() -> FastAPI:

    app = FastAPI(
        title="Seedr API",
        description="A comprehensive REST API wrapper for Seedr - Cloud torrent downloader",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(account.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(torrents.router, prefix="/api/v1")
    app.include_router(vlc.router, prefix="/api/v1")

    @app.get("/", tags=["General"])
    def index():
        return {
            "message": "Welcome to Seedr API",
            "documentation": "/docs",
            "version": "1.0.0",
            "endpoints": {
                "authentication": "/api/v1/auth",
                "account": "/api/v1/account",
                "files": "/api/v1/files",
                "torrents": "/api/v1/torrents",
                "vlc": "/api/v1/vlc"
            }
        }
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
