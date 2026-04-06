import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establish database connection"""
    try:
        conn = pymysql.connect(
            host=os.environ.get('DATABASE_HOST', 'localhost'),
            user=os.environ.get('DATABASE_USER', 'root'),
            password=os.environ.get('DATABASE_PASSWORD', ''),
            database=os.environ.get('DATABASE_NAME', 'skilltracker'),
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.Error as e:
        print(f"Database connection error: {e}")
        return None

def fix_foreign_key():
    """Fix the foreign key constraint in users table"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # Check if roles table exists and has data
        cursor.execute("SELECT COUNT(*) as count FROM roles")
        roles_count = cursor.fetchone()['count']
        print(f"Roles table has {roles_count} records")

        if roles_count == 0:
            # Insert default roles
            cursor.execute("""
                INSERT IGNORE INTO roles (role_name, description) VALUES
                ('admin', 'Administrator with full system access'),
                ('user', 'Regular user with limited access')
            """)
            print("Inserted default roles")

        # Check current foreign key
        cursor.execute("""
            SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'skilltracker' AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role_ID'
        """)
        fk_info = cursor.fetchone()
        print(f"Current FK info: {fk_info}")
        if fk_info:
            print(f"Current FK: {fk_info}")
            if fk_info['REFERENCED_TABLE_NAME'] != 'roles' or fk_info['REFERENCED_COLUMN_NAME'] != 'role_ID':
                # Drop old foreign key
                drop_sql = f"ALTER TABLE users DROP FOREIGN KEY {fk_info['CONSTRAINT_NAME']}"
                print(f"Executing: {drop_sql}")
                cursor.execute(drop_sql)
                print(f"Dropped old FK: {fk_info['CONSTRAINT_NAME']}")

                # Add new foreign key
                add_sql = "ALTER TABLE users ADD FOREIGN KEY (role_ID) REFERENCES roles(role_ID)"
                print(f"Executing: {add_sql}")
                cursor.execute(add_sql)
                print("Added new FK to roles(role_ID)")

        conn.commit()
        print("Foreign key fixed successfully")
        return True

    except Exception as e:
        print(f"Error fixing foreign key: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = fix_foreign_key()
    print("Fix completed" if success else "Fix failed")