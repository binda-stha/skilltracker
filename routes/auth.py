from flask import Blueprint, render_template, request, redirect, url_for, flash, session

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template("login.html")

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        role = request.form.get("role")

        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Admin Secret Key
        ADMIN_SECRET = "SKILLTRACKER-ADMIN-2025"

        # ---- VALIDATIONS ----
        if password != cpassword:
            flash("Passwords do not match!")
            return redirect(url_for("auth.register"))

        if role == "admin":
            secret_key = request.form.get("secret_key")
            if secret_key != ADMIN_SECRET:
                flash("Invalid Admin Secret Key!")
                return redirect(url_for("auth.register"))

        # ---- Insert into MySQL ----
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
                (email, hashed_password, role)
            )
            conn.commit()
            flash("Registration successful! Please login now.")
            return redirect(url_for("auth.login"))

        except:
            flash("Email already exists or error saving data.")
            return redirect(url_for("auth.register"))

        finally:
            conn.close()

    # GET request: show form
    return render_template("register.html")
