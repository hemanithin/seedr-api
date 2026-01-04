import logging
from flask import Flask, request
from flask_restx import Api
from config import Config
from routes import auth_ns, account_ns, files_ns, torrents_ns, vlc_ns


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure Logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request_info():
        """Log details about the incoming request"""
        logger.info(f"Request started: {request.method} {request.path}")
        logger.debug(f"Headers: {request.headers}")
        if request.get_json(silent=True):
            logger.debug(f"Body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response_info(response):
        """Log details about the response"""
        logger.info(f"Request finished: {request.method} {request.path} - Status: {response.status}")
        return response
    
    # Initialize Flask-RESTX API with Swagger documentation
    api = Api(
        app,
        version='1.0',
        title='Seedr API',
        description='A comprehensive REST API wrapper for Seedr - Cloud torrent downloader',
        doc='/docs',
        prefix='/api/v1'
    )
    
    # Register namespaces
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(account_ns, path='/account')
    api.add_namespace(files_ns, path='/files')
    api.add_namespace(torrents_ns, path='/torrents')
    api.add_namespace(vlc_ns, path='/vlc')
    
    # Initialize default authentication if enabled
    if app.config.get('DEFAULT_AUTH'):
        from utils import client_manager
        client_manager.initialize_default_auth()
    
    @api.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions"""
        logging.exception("An unhandled exception occurred")
        return {
            'error': str(error),
            'message': 'An unexpected error occurred'
        }, 500
    
    @app.route('/')
    def index():
        """Redirect to API documentation"""
        return {
            'message': 'Welcome to Seedr API',
            'documentation': '/docs',
            'version': '1.0',
            'endpoints': {
                'authentication': '/api/v1/auth',
                'account': '/api/v1/account',
                'files': '/api/v1/files',
                'torrents': '/api/v1/torrents',
                'vlc': '/api/v1/vlc'
            }
        }
    

    
    return app


if __name__ == '__main__':
    app = create_app()
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                     Seedr API Server                      ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Server running on: http://{Config.HOST}:{Config.PORT}              ║
    ║  Swagger UI:        http://{Config.HOST}:{Config.PORT}/docs         ║
    ║                                                           ║
    ║  API Endpoints:                                           ║
    ║  • Authentication: /api/v1/auth                           ║
    ║  • Account:        /api/v1/account                        ║
    ║  • Files:          /api/v1/files                          ║
    ║  • Torrents:       /api/v1/torrents                       ║
    ║  • VLC Player:     /api/v1/vlc                            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
