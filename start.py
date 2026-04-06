                      
"""
SkillTracker Startup Script
Ensures database is set up and starts the application
"""

import os
import sys
import subprocess

def setup_database():
    """Set up the database if needed"""
    print("Setting up database...")
    try:
        result = subprocess.run([sys.executable, 'setup_db.py'],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("Database setup successful")
            return True
        else:
            print(f"Database setup failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Database setup error: {e}")
        return False

def start_application():
    """Start the Flask application"""
    print("Starting SkillTracker application...")
    try:
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skilltracker', 'app.py')
        subprocess.Popen([sys.executable, app_path])
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")

def main():
    """Main startup function"""
    print("SkillTracker Startup")
    print("=" * 30)

                                
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

                    
    if not setup_database():
        print("Failed to set up database. Please check MySQL connection.")
        return

    print("\\n" + "=" * 30)
    print("Database ready!")
    print("Starting application...")
    print("Open http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop the application")
    print("=" * 30 + "\\n")

                       
    start_application()

if __name__ == "__main__":
    main()