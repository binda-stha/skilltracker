from flask import Blueprint, render_template, request, redirect, url_for, flash
import pymysql

auth = Blueprint('auth', __name__)

# ---------- DB CONNECTION FUNCTION ----------
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",  # your XAMPP MySQL password (empty if none)
        database="skilltracker",
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------- REGISTER ROUTE ----------
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        cpassword = request.form.get('cpassword', '')
        role = request.form.get('role', 'user')

        if not email or not password:
            flash("Email and password are required", "error")
            return render_template('register.html')
        
        if password != cpassword:
            flash("Passwords do not match", "error")
            return render_template('register.html')
        
        # Determine role_ID based on selected role
        if role == 'admin':
            role_ID = 1
            # Check admin secret key
            secret_key = request.form.get('secret_key', '')
            if secret_key != 'admin123':
                flash("Invalid admin secret key", "error")
                return render_template('register.html')
        else:
            role_ID = 2

        # ALL THIS CODE MUST BE INDENTED (8 spaces from left)
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash("Email already registered", "error")
            cursor.close()
            conn.close()
            return render_template('register.html')

        try:
            # Insert into database
            cursor.execute("""
                INSERT INTO users (email, password, role_ID)
                VALUES (%s, %s, %s)
            """, (email, password, role_ID))

            conn.commit()
            cursor.close()
            conn.close()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "error")
            cursor.close()
            conn.close()
            return render_template('register.html')

    return render_template('register.html')

# ---------- LOGIN ROUTE ----------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        role=request.form.get('role','user')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            # Check if the role matches
            if role == 'admin' and user['role_ID'] == 1:
                # Admin login successful
                flash("Admin login successful!", "success")
                return redirect(url_for('auth.admin_dashboard'))  #   # Redirect to admin dashboard
            
            elif role == 'user' and user['role_ID'] == 2:
                # User login successful
                flash("User login successful!", "success")
                return redirect(url_for('auth.user_dashboard'))   # Redirect to user dashboard
            
            else:
                # Role mismatch
                flash("Invalid credentials for selected role", "error")
                return redirect(url_for('auth.login'))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for('auth.login'))

    return render_template('login.html')


# ---------- ADMIN DASHBOARD ----------
@auth.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# ---------- USER DASHBOARD ----------
@auth.route('/user/dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')