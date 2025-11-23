import pymysql
from flask import Flask
from routes.auth import auth

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Manual MySQL connection
def get_db_connection():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",   # default XAMPP MySQL password is empty
        database="skilltracker",
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

# Register routes
app.register_blueprint(auth)

@app.route('/')
def home():
    return "Welcome to Daily Skill Tracker!"

if __name__ == "__main__":
    app.run(debug=True)
