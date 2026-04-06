"""
SkillTracker Application
BCA 6th Semester Project II - Tribhuvan University
Purpose: Daily Skill Tracking System with Progress Management
Author: Binda Shrestha
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask_session import Session
from routes.auth import auth

                                        
                                           
load_dotenv()

                               
app = Flask(__name__)

                                    
                                                                                     
flask_secret_key = os.environ.get('FLASK_SECRET_KEY')
if not flask_secret_key or flask_secret_key == 'your-secret-key-here-change-in-production':
                                                                    
    flask_secret_key = os.urandom(32).hex()
    print("⚠️  WARNING: Using generated SECRET_KEY. Set FLASK_SECRET_KEY in .env for production.")

app.secret_key = flask_secret_key

                                   
                                           
if not os.path.exists('logs'):
    os.mkdir('logs')

                   
log_file = os.environ.get('LOG_FILE', 'logs/skilltracker.log')
log_level = os.environ.get('LOG_LEVEL', 'INFO')

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10240000,        
    backupCount=10
)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)

log_level_value = getattr(logging, log_level.upper(), logging.INFO)
file_handler.setLevel(log_level_value)
app.logger.addHandler(file_handler)
app.logger.setLevel(log_level_value)

                                   
                                                         
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True                        
app.config['SESSION_KEY_PREFIX'] = 'skilltracker_'

                                            
session_lifetime_days = int(os.environ.get('SESSION_LIFETIME_DAYS', '7'))
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * session_lifetime_days

                                   
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')

Session(app)

                                 
app.register_blueprint(auth)

                        
@app.route('/')
def home():
    """Root route - redirects to login"""
    return redirect(url_for('auth.login'))

                            
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

                                   
if __name__ == "__main__":
                                                  
    app_host = os.environ.get('APP_HOST', 'localhost')
    app_port = int(os.environ.get('APP_PORT', '5000'))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.logger.info(f'Starting SkillTracker Application...')
    app.logger.info(f'Listening on http://{app_host}:{app_port}')
    app.logger.info(f'Debug mode: {debug_mode}')
    
    print("=" * 60)
    print("🚀 SkillTracker Application Starting")
    print(f"📍 Access at: http://{app_host}:{app_port}")
    print(f"🐛 Debug Mode: {debug_mode}")
    print("=" * 60)
    
    app.run(debug=debug_mode, host=app_host, port=app_port)
