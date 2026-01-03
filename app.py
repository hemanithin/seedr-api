from flask import Flask
from flask_restx import Api
from config import Config
from routes import auth_ns, account_ns, files_ns, torrents_ns, vlc_ns


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
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
    
    # Add custom error handlers
    @api.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions"""
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
            'web_tester': '/test',
            'version': '1.0',
            'endpoints': {
                'authentication': '/api/v1/auth',
                'account': '/api/v1/account',
                'files': '/api/v1/files',
                'torrents': '/api/v1/torrents',
                'vlc': '/api/v1/vlc'
            }
        }
    
    @app.route('/test')
    def test_interface():
        """Serve the API testing web interface"""
        from flask import render_template
        return render_template(
            'index.html',
            default_username=app.config.get('DEFAULT_USERNAME'),
            default_password=app.config.get('DEFAULT_PASSWORD'),
            default_auth=app.config.get('DEFAULT_AUTH', False)
        )
    
    return app


if __name__ == '__main__':
    app = create_app()
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                     Seedr API Server                      ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Server running on: http://{Config.HOST}:{Config.PORT}              ║
    ║  Swagger UI:        http://{Config.HOST}:{Config.PORT}/docs         ║
    ║  Web Tester:        http://{Config.HOST}:{Config.PORT}/test         ║
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
