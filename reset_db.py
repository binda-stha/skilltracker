#!/usr/bin/env python3
"""
SkillTracker Database Reset Script
Drops and recreates the database from scratch
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

def reset_database():
    """Drop and recreate the database"""
    print("🔄 Resetting database...")
    
    # Connect without database selection
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # Drop existing database
        print("  Dropping existing database...")
        cursor.execute("DROP DATABASE IF EXISTS skilltracker")
        conn.commit()
        print("  ✅ Database dropped")
        
        cursor.close()
        conn.close()
        return True
    except pymysql.Error as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

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
    
    # Connect without database selection first
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # Execute the entire schema
        print("  Executing schema...")
        statements = schema_sql.split(';')
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except pymysql.Error as e:
                    print(f"  ⚠️  Statement {i}: {e}")
                    # Continue with other statements
        
        conn.commit()
        print("  ✅ Database schema created")
        return True
    except pymysql.Error as e:
        print(f"  ❌ Database initialization failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_database():
    """Verify all required tables exist"""
    print("🔍 Verifying database...")
    
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
            print(f"  ❌ Missing tables: {', '.join(missing)}")
            return False
        
        print(f"  ✅ All {len(required_tables)} required tables found!")
        return True
    except pymysql.Error as e:
        print(f"  ❌ Verification failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main reset function"""
    print("\n" + "="*50)
    print("  SkillTracker Database Reset")
    print("="*50 + "\n")
    
    # Step 1: Reset database
    if not reset_database():
        print("\n❌ Failed to reset database")
        sys.exit(1)
    
    # Step 2: Initialize database
    if not init_database():
        print("\n❌ Failed to initialize database")
        sys.exit(1)
    
    # Step 3: Verify database
    if not verify_database():
        print("\n❌ Failed to verify database")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("✅ Database reset complete!")
    print("="*50 + "\n")
    print("Test accounts:")
    print("  Admin: admin@skilltracker.com / admin123")
    print("  User: student@skilltracker.com / password123")
    print()

if __name__ == '__main__':
    main()
