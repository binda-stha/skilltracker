#!/usr/bin/env python3
import pymysql
from werkzeug.security import generate_password_hash

# Generate correct hashes
admin_hash = generate_password_hash('admin123', method='pbkdf2:sha256', salt_length=16)
user_hash = generate_password_hash('password123', method='pbkdf2:sha256', salt_length=16)

print(f"Admin hash: {admin_hash}")
print(f"User hash: {user_hash}")

conn = pymysql.connect(host='localhost', user='root', password='', database='skilltracker')
c = conn.cursor()

# Update passwords
c.execute("UPDATE users SET password=%s WHERE email='admin@skilltracker.com'", (admin_hash,))
c.execute("UPDATE users SET password=%s WHERE email='student@skilltracker.com'", (user_hash,))

conn.commit()
print("\n✅ Passwords updated successfully!")

# Verify
c.execute("SELECT email, password FROM users")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1][:30]}...")

c.close()
conn.close()
