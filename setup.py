#!/usr/bin/env python3
"""
SkillTracker Setup and Initialization Script
This script initializes the database and validates the application
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection(database=None):
    """Create database connection"""
    try:
        config = {
            'host': os.environ.get('DATABASE_HOST', 'localhost'),
            'user': os.environ.get('DATABASE_USER', 'root'),
            'password': os.environ.get('DATABASE_PASSWORD', ''),
            'port': int(os.environ.get('DATABASE_PORT', '3306')),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        if database:
            config['database'] = database
        return pymysql.connect(**config)
    except pymysql.Error as e:
        print(f"❌ Database connection failed: {e}")
        return None

def init_database():
    """Initialize the database with schema"""
    print("🔄 Initializing database...")
    
    # Read schema file
    schema_file = 'database_schema.sql'
    if not os.path.exists(schema_file):
        print(f"❌ Schema file '{schema_file}' not found!")
        return False
    
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    
    # Connect and execute schema
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # Split and execute each statement
        statements = schema_sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        conn.commit()
        print("✅ Database initialized successfully!")
        return True
    except pymysql.Error as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_database():
    """Verify all required tables exist"""
    print("🔍 Verifying database tables...")
    
    required_tables = [
        'users', 'roles', 'skills', 'skill_logs', 'progress_log',
        'user_profile', 'education', 'experience', 'projects', 'certifications'
    ]
    
    conn = get_db_connection('skilltracker')
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TABLE_NAME FROM information_schema.tables
            WHERE TABLE_SCHEMA = 'skilltracker'
        """)
        existing_tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        
        missing = [t for t in required_tables if t not in existing_tables]
        if missing:
            print(f"❌ Missing tables: {', '.join(missing)}")
            return False
        
        print(f"✅ All {len(required_tables)} required tables found!")
        return True
    except pymysql.Error as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_files():
    """Verify all required files exist"""
    print("🔍 Verifying required files...")
    
    required_files = [
        'skilltracker/app.py',
        'skilltracker/routes/auth.py',
        'skilltracker/algorithms.py',
        'skilltracker/templates/login.html',
        'skilltracker/templates/register.html',
        'skilltracker/static/style.css',
        'requirements.txt',
        '.env'
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print(f"✅ All {len(required_files)} required files found!")
    return True

def main():
    """Main setup function"""
    print("\n" + "="*50)
    print("  SkillTracker Setup & Initialization")
    print("="*50 + "\n")
    
    # Verify files
    if not verify_files():
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        sys.exit(1)
    
    # Verify database
    if not verify_database():
        sys.exit(1)
    
    print("\n" + "="*50)
    print("✅ Setup complete! The application is ready to run.")
    print("="*50)
    print("\nTo start the application, run:")
    print("  python start.py")
    print("\nDefault test accounts:")
    print("  Admin: admin@skilltracker.com / admin123")
    print("  User: student@skilltracker.com / password123")
    print()

if __name__ == '__main__':
    main()
