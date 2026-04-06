import pymysql
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection(database=None):
    """Establish database connection"""
    try:
        conn = pymysql.connect(
            host=os.environ.get('DATABASE_HOST', 'localhost'),
            user=os.environ.get('DATABASE_USER', 'root'),
            password=os.environ.get('DATABASE_PASSWORD', ''),
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.Error as e:
        print(f"Database connection error: {e}")
        return None

def create_database():
    """Create database if it doesn't exist"""
    try:
        conn = pymysql.connect(
            host=os.environ.get('DATABASE_HOST', 'localhost'),
            user=os.environ.get('DATABASE_USER', 'root'),
            password=os.environ.get('DATABASE_PASSWORD', '')
        )
        cursor = conn.cursor()
        db_name = os.environ.get('DATABASE_NAME', 'skilltracker')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()
        return True
    except pymysql.Error as e:
        print(f"Error creating database: {e}")
        return False

def execute_sql_file(filename):
    """Execute SQL commands from file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        db_name = os.environ.get('DATABASE_NAME', 'skilltracker')
        conn = get_db_connection(database=db_name)
        if not conn:
            return False

        cursor = conn.cursor()

                                             
        commands = sql_content.split(';')
        for command in commands:
            command = command.strip()
            if command and not command.startswith('--'):
                try:
                    cursor.execute(command)
                except pymysql.Error as e:
                    if "Duplicate entry" not in str(e):                               
                        print(f"Warning executing command: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        print(f"SQL file '{filename}' executed successfully")
        return True

    except Exception as e:
        print(f"Error executing SQL file: {e}")
        return False

def ensure_roles_table():
    """Ensure roles table exists and migrate legacy role table if necessary"""
    try:
        db_name = os.environ.get('DATABASE_NAME', 'skilltracker')
        conn = get_db_connection(database=db_name)
        if not conn:
            return False

        cursor = conn.cursor()

                                    
        cursor.execute("SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema=%s AND table_name='role'", ('skilltracker',))
        legacy_role_exists = cursor.fetchone().get('cnt', 0) > 0

        cursor.execute("SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema=%s AND table_name='roles'", ('skilltracker',))
        roles_exists = cursor.fetchone().get('cnt', 0) > 0

        if not roles_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    role_ID INT PRIMARY KEY AUTO_INCREMENT,
                    role_name VARCHAR(50) UNIQUE NOT NULL,
                    description VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

        if legacy_role_exists and not roles_exists:
            cursor.execute("INSERT IGNORE INTO roles (role_name, description) SELECT rolename, 'Migrated from legacy role table' FROM role")

        conn.commit()
        cursor.close()
        conn.close()

        print("roles table checked and ensured")
        return True

    except Exception as e:
        print(f"Error ensuring roles table: {e}")
        return False

def test_database():
    """Test database connection and basic queries"""
    try:
        db_name = os.environ.get('DATABASE_NAME', 'skilltracker')
        conn = get_db_connection(database=db_name)
        if not conn:
            return False

        cursor = conn.cursor()

                            
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()['count']

                                                          
        cursor.execute("SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema=%s AND table_name='roles'", ('skilltracker',))
        roles_exists = cursor.fetchone()['count'] > 0

        if roles_exists:
            cursor.execute("SELECT COUNT(*) as count FROM roles")
            roles_count = cursor.fetchone()['count']
        else:
            cursor.execute("SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema=%s AND table_name='role'", ('skilltracker',))
            legacy_roles_exists = cursor.fetchone()['count'] > 0
            roles_count = 0
            if legacy_roles_exists:
                cursor.execute("SELECT COUNT(*) as count FROM role")
                roles_count = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        print(f"Database test passed - {users_count} users, {roles_count} role records")
        return True

    except Exception as e:
        print(f"Database test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("SkillTracker Database Setup")
    print("=" * 40)

                              
    sql_file = "database_schema.sql"
    if not os.path.exists(sql_file):
        print(f"SQL file '{sql_file}' not found")
        return False

                             
    if not create_database():
        return False

                            
    if not execute_sql_file(sql_file):
        return False

                                                                   
    if not ensure_roles_table():
        return False

                           
    if not test_database():
        return False

    print("\nDatabase setup completed successfully!")
    print("The SkillTracker database is ready for use.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)