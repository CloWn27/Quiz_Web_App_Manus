# app.py - Main Flask Application for FiSi-Quiz-Cyberpunk

import logging
import os
from datetime import timedelta

from flask import Flask, render_template, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import configuration
from config import get_config
# Import extensions
from extensions import db, migrate, socketio
# Import models
import models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    # Setup CORS
    cors_origins = config.CORS_ORIGINS
    if cors_origins == '*':
        CORS(app, origins="*")
    else:
        CORS(app, origins=cors_origins.split(',') if cors_origins else ["http://localhost:5000"])
    
    # Setup rate limiting
    if config.RATELIMIT_ENABLED:
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[config.RATELIMIT_DEFAULT],
            storage_uri=config.RATELIMIT_STORAGE_URL
        )
        limiter.init_app(app)
    
    # Register blueprints
    from views.main_routes import main_bp
    from views.auth_routes import auth_bp
    from views.game_routes import game_bp
    from views.admin_routes import admin_bp
    from views.profile_routes import profile_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    # Import SocketIO event handlers
    import socketio_events
    
    # Create database tables and initialize data
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
        
        # Initialize default data
        from utils.init_data import initialize_default_data
        initialize_default_data()
        logger.info("Default data initialized")
    
    # Configure session
    app.permanent_session_lifetime = timedelta(seconds=config.PERMANENT_SESSION_LIFETIME)
    
    # Add template context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'current_lang': session.get('lang', 'de'),
            'app_name': 'FiSi-Quiz Cyberpunk'
        }
    
    return app

def display_startup_info(config):
    """Display startup information"""
    print("\n" + "="*70)
    print("🌃 FiSi-Quiz-Cyberpunk - SYSTEM ONLINE")
    print("="*70)
    print(f"🌐 Server: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"🎮 Mode: {'Development' if config.FLASK_DEBUG else 'Production'}")
    print(f"🗄️  Database: {config.SQLALCHEMY_DATABASE_URI.split('://')[0]}")
    print(f"🔒 Security: {'Enhanced' if not config.FLASK_DEBUG else 'Development'}")
    print(f"🌍 CORS: {'All origins' if config.CORS_ORIGINS == '*' else 'Restricted'}")
    print("\n📱 Access Points:")
    print(f"   • Landing Page: http://{config.FLASK_HOST}:{config.FLASK_PORT}/")
    print(f"   • Dashboard: http://{config.FLASK_HOST}:{config.FLASK_PORT}/dashboard")
    print(f"   • Admin Panel: http://{config.FLASK_HOST}:{config.FLASK_PORT}/admin")
    print(f"   • Join Game: http://{config.FLASK_HOST}:{config.FLASK_PORT}/game/join")
    print("\n💡 Tips:")
    print("   • Default language: German (DE)")
    print("   • Cyberpunk theme enabled")
    print("   • Real-time multiplayer via SocketIO")
    print("="*70 + "\n")

if __name__ == '__main__':
    app = create_app()
    config = get_config()
    
    # Display startup information
    display_startup_info(config)
    
    # Setup graceful shutdown
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\n🚫 Shutting down FiSi-Quiz-Cyberpunk...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run development server
    try:
        logger.info("Starting SocketIO server...")
        socketio.run(app, 
                    host=config.FLASK_HOST, 
                    port=config.FLASK_PORT, 
                    debug=config.FLASK_DEBUG,
                    allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🚫 Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
