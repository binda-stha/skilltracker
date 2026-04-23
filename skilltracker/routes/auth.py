"""
Authentication & Skill Management Routes
Handles: Registration, Login, Logout, Skill CRUD, Progress Tracking, CV Generation
Security: Password hashing, session validation, input sanitization
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, current_app, jsonify, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from pymysql.err import InternalError
import os
import re
from datetime import datetime
import csv
import io
import time
import secrets
from skilltracker.algorithms import merge_sort_skills, get_top_skill_recommendations

auth = Blueprint('auth', __name__)

PUBLIC_AUTH_ENDPOINTS = {
    'auth.login',
    'auth.register',
    'auth.logout'
}

ADMIN_ONLY_ENDPOINTS = {
    'auth.admin_dashboard',
    'auth.admin_users',
    'auth.admin_skills',
    'auth.admin_analytics',
    'auth.admin_logs',
    'auth.admin_settings'
}


def validate_session():
    """Validate current session integrity"""
    required_keys = ['user_id', 'role_ID', 'email']
    for key in required_keys:
        if key not in session:
            return False
    if 'login_time' in session:
        try:
            login_time = datetime.fromisoformat(session['login_time'])
            if (datetime.now() - login_time).total_seconds() > 86400:
                return False
        except Exception:
            return False
    return True

def generate_csrf_token():
    """Generate CSRF token for forms"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token from form submission"""
    if token and secrets.compare_digest(token, session.get('csrf_token', '')):
        session['csrf_token'] = secrets.token_hex(32)  # Regenerate after successful validation
        return True
    return False

@auth.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf_token()}


@auth.before_request
def enforce_session_and_role_rules():
    """Centralized session integrity and role enforcement for auth blueprint routes."""
    endpoint = request.endpoint
    if not endpoint or not endpoint.startswith('auth.'):
        return None

    if endpoint in PUBLIC_AUTH_ENDPOINTS:
        return None

    if endpoint in ADMIN_ONLY_ENDPOINTS:
        if not validate_session() or session.get('role_ID') != 1:
            session.clear()
            flash("❌ Session expired. Please login again", "error")
            return redirect(url_for('auth.login'))
        return None

    # All remaining auth blueprint routes are user-only.
    if not validate_session() or session.get('role_ID') != 2:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    return None


def get_db_connection():
    """Establish database connection"""
    try:
        conn = pymysql.connect(
            host=os.environ.get('DATABASE_HOST', 'localhost'),
            user=os.environ.get('DATABASE_USER', 'root'),
            password=os.environ.get('DATABASE_PASSWORD', ''),
            database=os.environ.get('DATABASE_NAME', 'skilltracker'),
            port=int(os.environ.get('DATABASE_PORT', '3306')),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.Error as e:
        current_app.logger.error(f"Database Error: {e}")
        return None


def user_profile_has_id_column(cursor):
    """Check if user_profile table has legacy 'id' column"""
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.columns "
        "WHERE table_schema=%s AND table_name=%s AND column_name='id'",
        ('skilltracker', 'user_profile')
    )
    row = cursor.fetchone()
    return row and row.get('cnt', 0) > 0


def ensure_user_profile_id_alias():
    """Add a virtual id alias column for user_profile if missing"""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        if not user_profile_has_id_column(cursor):
            cursor.execute(
                "ALTER TABLE user_profile ADD COLUMN id INT GENERATED ALWAYS AS (profile_id) VIRTUAL"
            )
            conn.commit()
    except pymysql.Error:
        pass
    finally:
        cursor.close()
        conn.close()


def build_user_dashboard_payload(user_id):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    def format_dashboard_date(value, output_format):
        if not value:
            return None
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        if hasattr(value, 'strftime'):
            return value.strftime(output_format)
        return str(value)

    try:
        cursor.execute("""
            SELECT skill_id, skill_name, description, current_progress, target_hours, priority, target_date, created_at
            FROM skills
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        skills = cursor.fetchall()
        skills = merge_sort_skills(skills, key='current_progress', reverse=True)

        total_skills = len(skills)
        progress_values = []
        for skill in skills:
            progress = float(skill['current_progress'] or 0)
            progress_values.append(progress)

        total_progress = sum(progress_values)
        average_progress = float(round(total_progress / total_skills, 2)) if total_skills else 0.0
        completed_skills = sum(1 for p in progress_values if p == 100)

        if average_progress >= 80:
            proficiency_level = "Advanced"
        elif average_progress >= 50:
            proficiency_level = "Intermediate"
        else:
            proficiency_level = "Beginner"

        cursor.execute("""
            SELECT s.skill_name, COALESCE(SUM(l.hours_spent), 0) as total_hours
            FROM skills s
            LEFT JOIN skill_logs l ON s.skill_id = l.skill_id AND l.user_id = s.user_id
            WHERE s.user_id = %s
            GROUP BY s.skill_name
            ORDER BY total_hours DESC
        """, (user_id,))
        hours_by_skill = cursor.fetchall()

        cursor.execute("""
            SELECT DATE(l.log_date) as date, COALESCE(SUM(l.hours_spent), 0) as daily_hours
            FROM skill_logs l
            WHERE l.user_id = %s AND l.log_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
            GROUP BY DATE(l.log_date)
            ORDER BY date
        """, (user_id,))
        weekly_data = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(hours_spent), 0) as total_hours FROM skill_logs WHERE user_id=%s", (user_id,))
        total_hours_result = cursor.fetchone()
        total_hours = total_hours_result['total_hours'] if total_hours_result else 0

        most_practiced_skill = hours_by_skill[0]['skill_name'] if hours_by_skill else "None"

        cursor.execute("""
            SELECT skill_name, current_progress
            FROM skills
            WHERE user_id = %s
            ORDER BY skill_name
        """, (user_id,))
        skill_distribution = cursor.fetchall()

        cursor.execute("""
            SELECT l.log_id, s.skill_name, l.hours_spent, l.log_date, l.reflection_notes
            FROM skill_logs l
            JOIN skills s ON l.skill_id = s.skill_id
            WHERE l.user_id = %s
            ORDER BY l.log_date DESC
            LIMIT 10
        """, (user_id,))
        recent_logs = cursor.fetchall()

        cursor.execute("""
            SELECT full_name FROM user_profile WHERE user_id = %s
        """, (user_id,))
        profile = cursor.fetchone()
        full_name = profile['full_name'] if profile and profile['full_name'] else "User"
        user_initials = ''.join([part[0].upper() for part in full_name.split() if part])[:2] or session.get('email', 'U')[0].upper()
        max_weekly = float(max((float(row['daily_hours'] or 0) for row in weekly_data), default=1))
        today = datetime.now().strftime("%A, %B %d, %Y")

        proficiency_breakdown = {
            'beginner': 0,
            'intermediate': 0,
            'advanced': 0,
            'expert': 0
        }
        for skill in skills:
            progress = skill['current_progress'] if skill['current_progress'] else 0
            if progress >= 90:
                proficiency_breakdown['expert'] += 1
            elif progress >= 70:
                proficiency_breakdown['advanced'] += 1
            elif progress >= 40:
                proficiency_breakdown['intermediate'] += 1
            else:
                proficiency_breakdown['beginner'] += 1

        # FIX: recommend_skill opens its own connection — call after cursor/conn are still open
        # but we close cursor before calling it to avoid nested connection issues
        cursor.close()
        conn.close()

        recommended_skill = recommend_skill(user_id)

        return {
            'full_name': full_name,
            'user_initials': user_initials,
            'today': today,
            'skills': [
                {
                    'skill_id': skill['skill_id'],
                    'skill_name': skill['skill_name'],
                    'description': skill['description'] or 'No description',
                    'current_progress': int(skill['current_progress'] or 0),
                    'target_hours': int(skill['target_hours'] or 0),
                    'priority': skill['priority'] or 'Medium',
                    'target_date': str(skill['target_date']) if skill['target_date'] else None,
                    'proficiency_level': calculate_proficiency_level(skill['current_progress'])
                }
                for skill in skills
            ],
            'average_progress': average_progress,
            'total_skills': total_skills,
            'completed_skills': completed_skills,
            'proficiency_level': proficiency_level,
            'recent_logs': [
                {
                    'log_id': log['log_id'],
                    'skill_name': log['skill_name'],
                    'hours_spent': int(log['hours_spent'] or 0),
                    'log_date': format_dashboard_date(log['log_date'], '%b %d, %Y') or 'N/A',
                    'reflection_notes': log['reflection_notes'] or ''
                }
                for log in recent_logs
            ],
            'total_hours': int(total_hours),
            'hours_by_skill': [
                {'skill_name': row['skill_name'], 'total_hours': float(row['total_hours'] or 0)}
                for row in hours_by_skill
            ],
            'weekly_data': [
                {
                    'date': format_dashboard_date(row['date'], '%Y-%m-%d') or '',
                    'weekday': format_dashboard_date(row['date'], '%a') or '',
                    'daily_hours': float(row['daily_hours'] or 0)
                }
                for row in weekly_data
            ],
            'max_weekly': max_weekly,
            'most_practiced_skill': most_practiced_skill,
            'skill_distribution': [
                {
                    'skill_name': row['skill_name'],
                    'current_progress': int(row['current_progress'] or 0)
                }
                for row in skill_distribution
            ],
            'proficiency_breakdown': proficiency_breakdown,
            'recommended_skill': recommended_skill
        }
    except Exception as e:
        current_app.logger.error(f"Error building dashboard payload: {str(e)}")
        return None
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_progress(progress_str):
    """Validate progress value (0-100)"""
    try:
        progress = int(progress_str)
        return 0 <= progress <= 100
    except (ValueError, TypeError):
        return False

def sanitize_input(text):
    """Remove special characters from input"""
    if not isinstance(text, str):
        return ""
    return text.strip()


def execute_safe_query(cursor, query, params=None, retries=1):
    """Handle transient 1412 table definition state changes."""
    try:
        if params is None:
            return cursor.execute(query)
        return cursor.execute(query, params)
    except InternalError as e:
        if e.args and e.args[0] == 1412 and retries > 0:
            try:
                cursor.connection.ping(reconnect=True)
            except Exception:
                pass
            time.sleep(0.05)
            return execute_safe_query(cursor, query, params=params, retries=retries-1)
        raise


def calculate_skill_progress(user_id, skill_id):
    """Recalculate and update skill progress based on logged hours and target_hours."""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = None  # FIX: initialise to None so finally block is safe
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT target_hours FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
        skill = cursor.fetchone()
        if not skill:
            return None

        target_hours = skill.get('target_hours') or 0
        if target_hours <= 0:
            return None

        cursor.execute("SELECT COALESCE(SUM(hours_spent), 0) as total_hours FROM skill_logs WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
        total_hours = cursor.fetchone().get('total_hours') or 0

        progress = min(100, round((float(total_hours) / float(target_hours)) * 100 if target_hours else 0, 2))
        proficiency_level = calculate_proficiency_level(progress)
        status = 'Completed' if progress >= 100 else 'Active'
        cursor.execute(
            "UPDATE skills SET current_progress=%s, proficiency_level=%s, status=%s, updated_at=NOW() "
            "WHERE skill_id=%s AND user_id=%s",
            (progress, proficiency_level, status, skill_id, user_id)
        )
        conn.commit()
        return progress

    except Exception as e:
        current_app.logger.error(f"calculate_skill_progress error: {e}")
        return None

    finally:
        # FIX: always close cursor if it was created
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def ensure_target_hours_column_exists():
    """Add target_hours column to skills table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM skills LIKE 'target_hours'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE skills ADD COLUMN target_hours INT DEFAULT 0")
            conn.commit()
    except Exception:
        pass
    finally:
        cursor.close()
        conn.close()


def ensure_priority_column_exists():
    """Add priority column to skills table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM skills LIKE 'priority'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE skills ADD COLUMN priority ENUM('Low','Medium','High') DEFAULT 'Medium'")
            conn.commit()
    except Exception:
        pass
    finally:
        cursor.close()
        conn.close()


def calculate_proficiency_level(progress):
    """Return proficiency level label based on current progress."""
    try:
        value = float(progress)
    except (TypeError, ValueError):
        return 'Beginner'

    if value >= 90:
        return 'Expert'
    if value >= 70:
        return 'Advanced'
    if value >= 40:
        return 'Intermediate'
    return 'Beginner'


def delete_user_item(table, id_col, item_id, user_id):
    """Generic delete helper for user items (education, experience, etc)"""
    conn = get_db_connection()
    if not conn:
        return False, "Database error"
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT user_id FROM {table} WHERE {id_col}=%s", (item_id,))
        item = cursor.fetchone()
        if not item or item['user_id'] != user_id:
            return False, "Unauthorized"
        cursor.execute(f"DELETE FROM {table} WHERE {id_col}=%s", (item_id,))
        conn.commit()
        return True, "Deleted"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def recommend_skill(user_id):
    """
    Skill Recommendation Algorithm (Greedy)

    Fetches all skills for the user, calculates a recommendation score
    based on remaining progress and priority, and returns the top skill.

    Returns:
        dict with skill_name, priority, progress, recommendation_score, improvement_potential
        or None if no skills found.
    """
    conn = get_db_connection()
    if not conn:
        return None

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT skill_id, skill_name, current_progress, COALESCE(priority, 'Medium') as priority
            FROM skills
            WHERE user_id = %s
        """, (user_id,))
        skills = cursor.fetchall()

        if not skills:
            return None

        skills_list = [
            {
                'id': skill['skill_id'],
                'name': skill['skill_name'],
                'progress': float(skill['current_progress'] or 0),
                'priority': skill['priority'].lower()
            }
            for skill in skills
        ]

        top_recommendation = get_top_skill_recommendations(skills_list, top_n=1)
        if not top_recommendation:
            return None

        rec = top_recommendation[0]
        return {
            'skill_name': rec['name'],
            'priority': rec['priority'],
            'progress': rec['progress'],
            'recommendation_score': round(rec['recommendation_score'], 1),
            'improvement_potential': round(100 - rec['progress'], 1)
        }

    except Exception as e:
        current_app.logger.error(f"Error in recommend_skill: {str(e)}")
        return None

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration Route
    POST: Create new user account
    GET: Display registration form
    """
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        cpassword = request.form.get('cpassword', '')
        role = request.form.get('role', 'user')

        if not email or not password:
            current_app.logger.warning(f'Registration incomplete from {request.remote_addr}')
            flash("Email and password are required", "error")
            return render_template('register.html')

        if not is_valid_email(email):
            current_app.logger.warning(f'Invalid email: {email}')
            flash("Invalid email format", "error")
            return render_template('register.html')

        if len(password) < 6:
            current_app.logger.warning(f'Weak password for {email}')
            flash("Password must be at least 6 characters", "error")
            return render_template('register.html')

        if password != cpassword:
            current_app.logger.warning(f'Password mismatch for {email}')
            flash("Passwords do not match", "error")
            return render_template('register.html')

        if role == 'admin':
            role_ID = 1
            secret_key = request.form.get('secret_key', '')
            configured_admin_secret = os.environ.get('ADMIN_REGISTRATION_SECRET')
            if not configured_admin_secret:
                current_app.logger.error('Admin registration blocked: ADMIN_REGISTRATION_SECRET missing')
                flash("Admin registration is disabled by server configuration", "error")
                return render_template('register.html')
            if not secrets.compare_digest(secret_key, configured_admin_secret):
                current_app.logger.warning('Invalid admin secret key')
                flash("Invalid admin secret key", "error")
                return render_template('register.html')
        else:
            role_ID = 2

        conn = get_db_connection()
        if not conn:
            current_app.logger.error(f'Reg DB error: {email}')
            flash("❌ Database connection failed", "error")
            return render_template('register.html')

        cursor = conn.cursor()

        try:
            execute_safe_query(cursor, "SELECT * FROM users WHERE email=%s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                current_app.logger.info(f'Registration attempt with duplicate email: {email}')
                flash("Email already registered", "error")
                return render_template('register.html')

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

            cursor.execute("""
                INSERT INTO users (email, password, role_ID, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (email, hashed_password, role_ID))

            conn.commit()

            role_name = 'Admin' if role_ID == 1 else 'User'
            current_app.logger.info(f'New {role_name}: {email}')

            flash("Registration successful! Please login.", "success")
            return redirect(url_for('auth.login'))

        except Exception as e:
            current_app.logger.error(f'Reg fail: {e}')
            flash(f"Registration failed: {str(e)}", "error")
            return render_template('register.html')

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    General Login Route - Handles both admin and user login
    POST: Authenticate user and start session
    GET: Display login form
    """
    if request.method == 'POST':
        try:
            email = sanitize_input(request.form.get('email', ''))
            password = request.form.get('password', '')
            role = request.form.get('role', 'user')

            if not email or not password:
                current_app.logger.warning('Login incomplete')
                flash("Email and password required", "error")
                return render_template('login.html')

            conn = get_db_connection()
            if not conn:
                current_app.logger.error(f'Login DB error: {email}')
                flash("Database connection failed", "error")
                return render_template('login.html')

            cursor = conn.cursor()
            execute_safe_query(cursor, "SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['password'], password):
                if (role == 'admin' and user['role_ID'] == 1) or (role == 'user' and user['role_ID'] == 2):
                    session.clear()
                    session['user_id'] = user['id']
                    session['role_ID'] = user['role_ID']
                    session['email'] = user['email']
                    session['login_time'] = datetime.now().isoformat()
                    session['session_token'] = secrets.token_hex(16)

                    role_name = 'Admin' if user['role_ID'] == 1 else 'User'
                    current_app.logger.info(f'{role_name} login: {email}')

                    if role == 'admin':
                        flash("Admin login successful!", "success")
                        return redirect(url_for('auth.admin_dashboard'))
                    else:
                        flash("Login successful!", "success")
                        return redirect(url_for('auth.user_dashboard'))
                else:
                    current_app.logger.warning(f'Role mismatch: {email}')
                    flash("Invalid credentials for selected role", "error")
            else:
                current_app.logger.warning(f'Login failed: {email}')
                flash("Invalid email or password", "error")

            return render_template('login.html')

        except Exception as e:
            current_app.logger.error(f'Login error: {e}')
            import traceback
            traceback.print_exc()
            flash(f"Login error: {str(e)}", "error")
            return render_template('login.html')

    return render_template('login.html')


@auth.route('/logout')
def logout():
    """Securely clear session and logout user"""
    email = session.get('email', 'unknown')
    current_app.logger.info(f'Logout: {email}')
    session.clear()
    response = make_response(redirect(url_for('auth.login')))
    flash("Logged out successfully", "success")
    return response


@auth.route('/admin/dashboard')
def admin_dashboard():
    """Display admin dashboard with all users and skills statistics"""
    if not validate_session() or session.get('role_ID') != 1:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.login'))

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, email, role_ID, "
            "CASE WHEN role_ID = 1 THEN 'Admin' ELSE 'User' END AS role_name, "
            "created_at FROM users ORDER BY created_at DESC"
        )
        users = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE role_ID=2")
        user_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as total_admins FROM users WHERE role_ID=1")
        admin_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as total_skills FROM skills")
        skill_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as total_logs FROM skill_logs")
        log_count = cursor.fetchone()

        cursor.execute("SELECT AVG(current_progress) as avg_progress FROM skills")
        avg_progress = cursor.fetchone()

        return render_template(
            'admin_dashboard.html',
            users=users,
            user_count=user_count['total_users'],
            admin_count=admin_count['total_admins'],
            skill_count=skill_count['total_skills'],
            log_count=log_count['total_logs'],
            avg_progress=round(avg_progress['avg_progress'] or 0, 2)
        )

    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.login'))

    finally:
        cursor.close()
        conn.close()


@auth.route('/admin/users')
def admin_users():
    """Admin users management page"""
    if not validate_session() or session.get('role_ID') != 1:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.admin_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, email, role_ID, "
            "CASE WHEN role_ID = 1 THEN 'Admin' ELSE 'User' END AS role_name, "
            "created_at FROM users ORDER BY created_at DESC"
        )
        users = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE role_ID=2")
        user_count = cursor.fetchone()

        return render_template(
            'admin_users.html',
            users=users,
            user_count=user_count['total_users']
        )
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.admin_dashboard'))
    finally:
        cursor.close()
        conn.close()


@auth.route('/admin/skills')
def admin_skills():
    """Admin skills management page"""
    if not validate_session() or session.get('role_ID') != 1:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.admin_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT s.skill_id, s.skill_name, s.user_id, s.current_progress, s.priority, u.email "
            "FROM skills s "
            "JOIN users u ON s.user_id = u.id "
            "ORDER BY s.created_at DESC"
        )
        skills = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total_skills FROM skills")
        skill_count = cursor.fetchone()

        return render_template(
            'admin_skills.html',
            skills=skills,
            skill_count=skill_count['total_skills']
        )
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.admin_dashboard'))
    finally:
        cursor.close()
        conn.close()


@auth.route('/admin/analytics')
def admin_analytics():
    """Admin analytics page"""
    if not validate_session() or session.get('role_ID') != 1:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.admin_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE role_ID=2")
        user_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as total_skills FROM skills")
        skill_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as total_logs FROM skill_logs")
        log_count = cursor.fetchone()

        cursor.execute("SELECT AVG(current_progress) as avg_progress FROM skills")
        avg_progress = cursor.fetchone()

        cursor.execute("SELECT priority, COUNT(*) as count FROM skills GROUP BY priority")
        priority_distribution = cursor.fetchall()

        return render_template(
            'admin_analytics.html',
            user_count=user_count['total_users'],
            skill_count=skill_count['total_skills'],
            log_count=log_count['total_logs'],
            avg_progress=round(avg_progress['avg_progress'] or 0, 2),
            priority_distribution=priority_distribution
        )
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.admin_dashboard'))
    finally:
        cursor.close()
        conn.close()


@auth.route('/admin/logs')
def admin_logs():
    """Admin logs management page"""
    if not validate_session() or session.get('role_ID') != 1:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.admin_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT l.log_id, l.user_id, l.skill_id, s.skill_name, l.hours_spent, l.log_date, u.email "
            "FROM skill_logs l "
            "JOIN skills s ON l.skill_id = s.skill_id "
            "JOIN users u ON l.user_id = u.id "
            "ORDER BY l.log_date DESC LIMIT 100"
        )
        logs = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total_logs FROM skill_logs")
        log_count = cursor.fetchone()

        return render_template(
            'admin_logs.html',
            logs=logs,
            log_count=log_count['total_logs']
        )
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.admin_dashboard'))
    finally:
        cursor.close()
        conn.close()


@auth.route('/admin/settings')
def admin_settings():
    """Admin settings page"""
    if not validate_session() or session.get('role_ID') != 1:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    return render_template('admin_settings.html')


@auth.route('/user/dashboard')
def user_dashboard():
    """Display user dashboard with skills summary and learning analytics"""
    if not validate_session() or session.get('role_ID') != 2:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    ensure_user_profile_id_alias()

    # FIX: removed the redundant duplicate DB queries that were here before.
    # build_user_dashboard_payload() does all the querying; calling it once is enough.
    payload = build_user_dashboard_payload(user_id)

    if payload is None:
        flash("❌ Error loading dashboard", "error")
        return redirect(url_for('auth.login'))

    try:
        return render_template('user_dashboard.html', **payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"❌ Error loading dashboard: {str(e)}", "error")
        return redirect(url_for('auth.login'))


@auth.route('/user/dashboard/data')
def user_dashboard_data():
    """JSON endpoint for user dashboard dynamic updates"""
    if not validate_session() or session.get('role_ID') != 2:
        session.clear()
        return jsonify({'error': 'Session expired or unauthorized'}), 401

    user_id = session['user_id']
    payload = build_user_dashboard_payload(user_id)
    if payload is None:
        return jsonify({'error': 'Unable to load dashboard data'}), 500

    return jsonify(payload)


@auth.route('/add-skill', methods=['GET', 'POST'])
def add_skill():
    """Add new skill for user"""
    if not validate_session() or session.get('role_ID') != 2:
        session.clear()
        flash("❌ Session expired. Please login again", "error")
        return redirect(url_for('auth.login'))

    ensure_target_hours_column_exists()
    ensure_priority_column_exists()

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            current_app.logger.warning('CSRF validation failed')
            flash("❌ Invalid request", "error")
            return redirect(url_for('auth.add_skill'))

        skill_name = sanitize_input(request.form.get('skill_name', ''))
        description = sanitize_input(request.form.get('description', ''))
        progress = request.form.get('progress', '0')
        target_date = request.form.get('target_date', None)
        target_hours = request.form.get('target_hours', '0')
        priority = request.form.get('priority', 'Medium').strip().capitalize()
        if priority not in ['Low', 'Medium', 'High']:
            priority = 'Medium'

        proficiency_level = calculate_proficiency_level(progress)

        if not skill_name:
            flash("❌ Skill name is required", "error")
            return render_template('add_skill.html')

        if not is_valid_progress(progress):
            flash("❌ Progress must be between 0 and 100", "error")
            return render_template('add_skill.html')

        try:
            target_hours_value = int(target_hours) if target_hours else 0
            if target_hours_value < 0:
                raise ValueError
        except ValueError:
            flash("❌ Target hours must be a non-negative integer", "error")
            return render_template('add_skill.html')

        conn = get_db_connection()
        if not conn:
            current_app.logger.error('Skill DB error')
            flash("❌ Database error", "error")
            return render_template('add_skill.html')

        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO skills (user_id, skill_name, description, current_progress, target_hours, priority, proficiency_level, target_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (session['user_id'], skill_name, description, int(progress), target_hours_value, priority, proficiency_level, target_date if target_date else None))

            conn.commit()
            current_app.logger.info(f'Skill added: {skill_name}')
            flash("✅ Skill added successfully!", "success")
            return redirect(url_for('auth.user_dashboard'))

        except Exception as e:
            current_app.logger.error(f'Add skill error: {e}')
            flash(f"❌ Error adding skill: {str(e)}", "error")
            return render_template('add_skill.html')

        finally:
            cursor.close()
            conn.close()

    return render_template('add_skill.html')


@auth.route('/edit-skill/<int:skill_id>', methods=['GET', 'POST'])
def edit_skill(skill_id):
    """Edit existing skill"""
    if 'user_id' not in session or not validate_session() or session.get('role_ID') != 2:
        session.clear()
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
        try:
            csrf_token = request.form.get('csrf_token')
            if not validate_csrf_token(csrf_token):
                current_app.logger.warning('CSRF validation failed')
                flash("❌ Invalid request", "error")
                cursor.execute("SELECT * FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
                skill = cursor.fetchone()
                return render_template('edit_skill.html', skill=skill)

            skill_name = sanitize_input(request.form.get('skill_name', ''))
            description = sanitize_input(request.form.get('description', ''))
            progress = request.form.get('progress', '0')
            target_date = request.form.get('target_date', None)
            target_hours = request.form.get('target_hours', '0')
            priority = request.form.get('priority', 'Medium').strip().capitalize()
            if priority not in ['Low', 'Medium', 'High']:
                priority = 'Medium'

            if not skill_name:
                flash("❌ Skill name is required", "error")
                cursor.execute("SELECT * FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
                skill = cursor.fetchone()
                return render_template('edit_skill.html', skill=skill)

            proficiency_level = calculate_proficiency_level(progress)
            if not is_valid_progress(progress):
                flash("❌ Progress must be between 0 and 100", "error")
                cursor.execute("SELECT * FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
                skill = cursor.fetchone()
                return render_template('edit_skill.html', skill=skill)

            try:
                if target_date:
                    datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                flash("❌ Target date must be in YYYY-MM-DD format", "error")
                cursor.execute("SELECT * FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
                skill = cursor.fetchone()
                return render_template('edit_skill.html', skill=skill)

            try:
                target_hours_value = float(target_hours) if target_hours else 0.0
                if target_hours_value < 0:
                    raise ValueError
                target_hours_value = int(target_hours_value)  # Convert to int after validation
            except ValueError:
                flash("❌ Target hours must be a non-negative number", "error")
                cursor.execute("SELECT * FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
                skill = cursor.fetchone()
                return render_template('edit_skill.html', skill=skill)

            cursor.execute("SELECT user_id FROM skills WHERE skill_id=%s", (skill_id,))
            skill = cursor.fetchone()

            if not skill or skill['user_id'] != user_id:
                flash("❌ Unauthorized access", "error")
                return redirect(url_for('auth.user_dashboard'))

            cursor.execute("""
                UPDATE skills
                SET skill_name=%s, description=%s, current_progress=%s, target_hours=%s, priority=%s, proficiency_level=%s, target_date=%s, updated_at=NOW()
                WHERE skill_id=%s AND user_id=%s
            """, (skill_name, description, int(progress), target_hours_value, priority, proficiency_level, target_date if target_date else None, skill_id, user_id))

            conn.commit()
            flash("✅ Skill updated successfully!", "success")

        except Exception as e:
            current_app.logger.error(f"Edit skill exception: {e}")
            flash("❌ An unexpected error occurred while updating the skill.", "error")
            try:
                cursor.execute("SELECT * FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
                skill = cursor.fetchone()
            except Exception:
                skill = None

            if skill:
                return render_template('edit_skill.html', skill=skill)
            return redirect(url_for('auth.user_dashboard'))

        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        return redirect(url_for('auth.user_dashboard'))

    # GET
    try:
        cursor.execute("""
            SELECT * FROM skills
            WHERE skill_id=%s AND user_id=%s
        """, (skill_id, user_id))
        skill = cursor.fetchone()

        if not skill:
            flash("❌ Skill not found", "error")
            return redirect(url_for('auth.user_dashboard'))

        return render_template('edit_skill.html', skill=skill)

    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.user_dashboard'))

    finally:
        cursor.close()
        conn.close()


@auth.route('/delete-skill/<int:skill_id>', methods=['POST'])
def delete_skill(skill_id):
    """Delete skill"""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        current_app.logger.warning('CSRF validation failed on delete_skill')
        flash("❌ Invalid request", "error")
        return redirect(url_for('auth.user_dashboard'))

    conn = get_db_connection()
    if not conn:
        current_app.logger.error('Delete skill DB error')
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()
    user_id = session['user_id']

    try:
        cursor.execute("SELECT user_id, skill_name FROM skills WHERE skill_id=%s", (skill_id,))
        skill = cursor.fetchone()

        if not skill or skill['user_id'] != user_id:
            current_app.logger.warning('Unauthorized delete')
            flash("❌ Unauthorized access", "error")
            return redirect(url_for('auth.user_dashboard'))

        skill_name = skill.get('skill_name', f'Skill #{skill_id}')

        cursor.execute("DELETE FROM skills WHERE skill_id=%s AND user_id=%s", (skill_id, user_id))
        conn.commit()

        current_app.logger.info(f'Skill deleted: {skill_name}')
        flash("✅ Skill deleted successfully!", "success")

    except Exception as e:
        current_app.logger.error(f'Delete skill error: {e}')
        flash(f"❌ Error deleting skill: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('auth.user_dashboard'))


def ensure_skill_logs_table_exists():
    """Create skill_logs table if missing"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_logs (
                log_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                skill_id INT NOT NULL,
                hours_spent DECIMAL(5,2) NOT NULL,
                log_date DATE NOT NULL,
                reflection_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cursor.execute("FLUSH TABLES")
    except Exception as e:
        print(f"Error ensuring skill_logs table: {e}")
    finally:
        cursor.close()
        conn.close()


@auth.route('/add-log', methods=['GET', 'POST'])
def add_log():
    """Add daily learning log for a skill"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    ensure_skill_logs_table_exists()

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            skill_id_raw = request.form.get('skill_id', '').strip()
            hours_spent_raw = request.form.get('hours_spent', '0').strip()
            log_date_raw = request.form.get('log_date', datetime.utcnow().strftime('%Y-%m-%d')).strip()
            reflection_notes = sanitize_input(request.form.get('reflection_notes', ''))

            if not skill_id_raw:
                flash("❌ Skill is required", "error")
                return redirect(url_for('auth.add_log'))

            try:
                skill_id = int(skill_id_raw)
            except ValueError:
                flash("❌ Invalid skill selection", "error")
                return redirect(url_for('auth.add_log'))

            if not hours_spent_raw:
                flash("❌ Hours are required", "error")
                return redirect(url_for('auth.add_log'))

            try:
                float_hours = float(hours_spent_raw)
                if float_hours <= 0:
                    raise ValueError("Hours must be positive")
            except ValueError:
                flash("❌ Hours must be a positive number", "error")
                return redirect(url_for('auth.add_log'))

            try:
                entry_date = datetime.strptime(log_date_raw, '%Y-%m-%d').date()
                if entry_date > datetime.utcnow().date():
                    flash("❌ Log date cannot be in the future", "error")
                    return redirect(url_for('auth.add_log'))
            except ValueError:
                flash("❌ Invalid date format", "error")
                return redirect(url_for('auth.add_log'))

            cursor.execute("SELECT user_id FROM skills WHERE skill_id=%s", (skill_id,))
            skill = cursor.fetchone()
            if not skill or skill['user_id'] != user_id:
                flash("❌ Unauthorized skill selection", "error")
                return redirect(url_for('auth.add_log'))

            cursor.execute("""
                INSERT INTO skill_logs (user_id, skill_id, hours_spent, log_date, reflection_notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, skill_id, float_hours, entry_date, reflection_notes))

            conn.commit()
            cursor.close()
            conn.close()

            calculate_skill_progress(user_id, skill_id)
            flash("✅ Log added successfully!", "success")
            return redirect(url_for('auth.view_logs'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f"❌ Error adding log: {str(e)}", "error")
            return redirect(url_for('auth.add_log'))

        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    # GET
    try:
        cursor.execute("SELECT skill_id, skill_name FROM skills WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        skills = cursor.fetchall()
    except Exception as e:
        flash(f"❌ Error fetching skills: {str(e)}", "error")
        skills = []
    finally:
        cursor.close()
        conn.close()

    return render_template('add_log.html', skills=skills, current_date=datetime.utcnow().strftime('%Y-%m-%d'))


@auth.route('/edit-log/<int:log_id>', methods=['GET', 'POST'])
@auth.route('/user/edit-log/<int:log_id>', methods=['GET', 'POST'])
def edit_log(log_id):
    """Edit existing skill log"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    ensure_skill_logs_table_exists()
    conn = get_db_connection()

    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    if request.method == 'POST':
        skill_id = request.form.get('skill_id')
        hours_spent = request.form.get('hours_spent', '0')
        log_date = request.form.get('log_date')
        reflection_notes = sanitize_input(request.form.get('reflection_notes', ''))

        if not skill_id or not hours_spent:
            flash("❌ Skill and hours are required", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.view_logs'))

        try:
            float_hours = float(hours_spent)
            if float_hours <= 0:
                raise ValueError("Hours must be positive")
        except ValueError:
            flash("❌ Hours must be a positive number", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.view_logs'))

        try:
            entry_date = datetime.strptime(log_date, '%Y-%m-%d').date()
            if entry_date > datetime.utcnow().date():
                flash("❌ Log date cannot be in the future", "error")
                cursor.close()
                conn.close()
                return redirect(url_for('auth.view_logs'))
        except ValueError:
            flash("❌ Invalid date format", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.view_logs'))

        try:
            cursor.execute("SELECT user_id, skill_id FROM skill_logs WHERE log_id=%s", (log_id,))
            log = cursor.fetchone()

            if not log or log['user_id'] != user_id:
                flash("❌ Unauthorized access", "error")
                return redirect(url_for('auth.view_logs'))

            old_skill_id = log['skill_id']

            cursor.execute("""
                UPDATE skill_logs
                SET skill_id=%s, hours_spent=%s, log_date=%s, reflection_notes=%s
                WHERE log_id=%s AND user_id=%s
            """, (skill_id, float_hours, log_date, reflection_notes, log_id, user_id))

            conn.commit()
            cursor.close()
            conn.close()

            calculate_skill_progress(user_id, old_skill_id)
            if old_skill_id != int(skill_id):
                calculate_skill_progress(user_id, int(skill_id))
            flash("✅ Log updated successfully!", "success")

        except Exception as e:
            flash(f"❌ Error updating log: {str(e)}", "error")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

        return redirect(url_for('auth.view_logs'))

    # GET
    try:
        cursor.execute("""
            SELECT l.log_id, l.skill_id, l.hours_spent, l.log_date, l.reflection_notes
            FROM skill_logs l
            WHERE l.log_id=%s AND l.user_id=%s
        """, (log_id, user_id))
        log = cursor.fetchone()

        if not log:
            flash("❌ Log not found", "error")
            return redirect(url_for('auth.view_logs'))

        cursor.execute("SELECT skill_id, skill_name FROM skills WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        skills = cursor.fetchall()

        return render_template('edit_log.html', log=log, skills=skills)

    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.view_logs'))

    finally:
        cursor.close()
        conn.close()


@auth.route('/view-logs')
def view_logs():
    """Show daily skill logs with reflections"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    try:
        ensure_skill_logs_table_exists()
    except Exception as e:
        print(f"Warning: ensure_skill_logs_table_exists failed: {e}")

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT l.log_id, l.skill_id, s.skill_name, l.hours_spent, l.log_date, l.reflection_notes, l.created_at
            FROM skill_logs l
            LEFT JOIN skills s ON l.skill_id = s.skill_id
            WHERE l.user_id = %s
            ORDER BY l.log_date DESC, l.created_at DESC
        """, (user_id,))
        logs = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(hours_spent), 0) as total_hours FROM skill_logs WHERE user_id=%s", (user_id,))
        total_hours_row = cursor.fetchone()
        total_hours = total_hours_row['total_hours'] if total_hours_row and 'total_hours' in total_hours_row else 0

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"❌ Error fetching logs: {str(e)}", "error")
        logs = []
        total_hours = 0
    finally:
        cursor.close()
        conn.close()

    return render_template('logs.html', logs=logs, total_hours=total_hours)


@auth.route('/delete-log/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    """Delete a skill log"""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        current_app.logger.warning('CSRF validation failed on delete_log')
        flash("❌ Invalid request", "error")
        return redirect(url_for('auth.view_logs'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id, skill_id FROM skill_logs WHERE log_id=%s", (log_id,))
        log = cursor.fetchone()
        if not log or log['user_id'] != user_id:
            flash("❌ Unauthorized action", "error")
            return redirect(url_for('auth.view_logs'))

        skill_id = log['skill_id']
        cursor.execute("DELETE FROM skill_logs WHERE log_id=%s AND user_id=%s", (log_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        calculate_skill_progress(user_id, skill_id)
        flash("✅ Log deleted successfully", "success")

    except Exception as e:
        flash(f"❌ Error deleting log: {str(e)}", "error")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    return redirect(url_for('auth.view_logs'))


@auth.route('/export-logs')
def export_logs_csv():
    """Export skill logs to CSV"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    ensure_skill_logs_table_exists()

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT l.log_id, s.skill_name, l.hours_spent, l.log_date, l.reflection_notes, l.created_at
            FROM skill_logs l
            LEFT JOIN skills s ON l.skill_id = s.skill_id
            WHERE l.user_id = %s
            ORDER BY l.log_date DESC
        """, (user_id,))
        logs = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Log ID', 'Skill Name', 'Hours Spent', 'Log Date', 'Reflection Notes', 'Created At'])

        for l in logs:
            writer.writerow([l['log_id'], l['skill_name'] or '', l['hours_spent'], l['log_date'], l['reflection_notes'] or '', l['created_at']])

        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=skill_logs.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response

    except Exception as e:
        flash(f"❌ Error exporting logs: {str(e)}", "error")
        return redirect(url_for('auth.view_logs'))
    finally:
        cursor.close()
        conn.close()


@auth.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile information"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    ensure_user_profile_id_alias()

    conn = get_db_connection()
    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name', ''))
        phone = sanitize_input(request.form.get('phone', ''))
        address = sanitize_input(request.form.get('address', ''))
        linkedin = sanitize_input(request.form.get('linkedin', ''))
        github = sanitize_input(request.form.get('github', ''))
        professional_summary = sanitize_input(request.form.get('professional_summary', ''))

        try:
            cursor.execute("SELECT profile_id FROM user_profile WHERE user_id=%s", (user_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE user_profile SET
                    full_name=%s, phone=%s, address=%s, linkedin=%s, github=%s, professional_summary=%s
                    WHERE user_id=%s
                """, (full_name, phone, address, linkedin, github, professional_summary, user_id))
            else:
                cursor.execute("""
                    INSERT INTO user_profile (user_id, full_name, phone, address, linkedin, github, professional_summary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, full_name, phone, address, linkedin, github, professional_summary))

            conn.commit()
            flash("✅ Profile updated successfully!", "success")
        except Exception as e:
            flash(f"❌ Error updating profile: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.user_dashboard'))

    try:
        cursor.execute("SELECT * FROM user_profile WHERE user_id=%s", (user_id,))
        profile = cursor.fetchone()
    except Exception:
        profile = None
    finally:
        cursor.close()
        conn.close()

    return render_template('edit_profile.html', profile=profile)


@auth.route('/add-education', methods=['GET', 'POST'])
def add_education():
    """Add education record"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            current_app.logger.warning('CSRF validation failed')
            flash("❌ Invalid request", "error")
            return redirect(url_for('auth.add_education'))

        degree = sanitize_input(request.form.get('degree', ''))
        field_of_study = sanitize_input(request.form.get('field_of_study', ''))
        institution = sanitize_input(request.form.get('institution', ''))
        # FIX: form sends start_date/end_date (date strings); extract year from them
        start_date_raw = request.form.get('start_date', '')
        end_date_raw = request.form.get('end_date', '')
        grade = sanitize_input(request.form.get('grade_gpa', ''))
        description = sanitize_input(request.form.get('description', ''))

        if not degree or not institution:
            flash("❌ Degree and institution are required", "error")
            return render_template('add_education.html')

        # Extract year integers from date strings (e.g. "2020-09-01" → 2020)
        try:
            start_year = int(start_date_raw[:4]) if start_date_raw else None
        except (ValueError, IndexError):
            start_year = None

        try:
            end_year = int(end_date_raw[:4]) if end_date_raw else None
        except (ValueError, IndexError):
            end_year = None

        conn = get_db_connection()
        if not conn:
            flash("❌ Database error", "error")
            return render_template('add_education.html')

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO education (user_id, degree, field_of_study, institution, start_year, end_year, gpa, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], degree, field_of_study, institution, start_year, end_year, grade, description))
            conn.commit()
            flash("✅ Education added successfully!", "success")
        except Exception as e:
            flash(f"❌ Error adding education: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.user_dashboard'))

    return render_template('add_education.html')


@auth.route('/add-experience', methods=['GET', 'POST'])
def add_experience():
    """Add work experience"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        job_title = sanitize_input(request.form.get('position', ''))
        company = sanitize_input(request.form.get('company', ''))
        location = sanitize_input(request.form.get('location', ''))
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        description = sanitize_input(request.form.get('description', ''))

        if not job_title or not company:
            flash("❌ Job title and company are required", "error")
            return render_template('add_experience.html')

        conn = get_db_connection()
        if not conn:
            flash("❌ Database error", "error")
            return render_template('add_experience.html')

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO experience (user_id, job_title, company, location, start_date, end_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], job_title, company, location, start_date, end_date, description))
            conn.commit()
            flash("✅ Experience added successfully!", "success")
        except Exception as e:
            flash(f"❌ Error adding experience: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.user_dashboard'))

    return render_template('add_experience.html')


@auth.route('/add-project', methods=['GET', 'POST'])
def add_project():
    """Add project"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        project_name = sanitize_input(request.form.get('project_name', ''))
        description = sanitize_input(request.form.get('description', ''))
        technologies = sanitize_input(request.form.get('technologies', ''))
        github_link = sanitize_input(request.form.get('github_link', ''))

        if not project_name:
            flash("❌ Project name is required", "error")
            return render_template('add_project.html')

        conn = get_db_connection()
        if not conn:
            flash("❌ Database error", "error")
            return render_template('add_project.html')

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO projects (user_id, project_name, description, technologies, github_link)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['user_id'], project_name, description, technologies, github_link))
            conn.commit()
            flash("✅ Project added successfully!", "success")
        except Exception as e:
            flash(f"❌ Error adding project: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.user_dashboard'))

    return render_template('add_project.html')


@auth.route('/add-certification', methods=['GET', 'POST'])
def add_certification():
    """Add certification"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        certificate_name = sanitize_input(request.form.get('certification_name', ''))
        organization = sanitize_input(request.form.get('issuing_organization', ''))
        year = request.form.get('year')
        expiry_date = request.form.get('expiry_date')
        credential_id = sanitize_input(request.form.get('credential_id', ''))

        if not certificate_name or not organization:
            flash("❌ Certificate name and organization are required", "error")
            return render_template('add_certification.html')

        issue_date = f"{year}-01-01" if year else None

        conn = get_db_connection()
        if not conn:
            flash("❌ Database error", "error")
            return render_template('add_certification.html')

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO certifications (user_id, certification_name, issuing_organization, issue_date, expiry_date, credential_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session['user_id'], certificate_name, organization, issue_date, expiry_date, credential_id))
            conn.commit()
            flash("✅ Certification added successfully!", "success")
        except Exception as e:
            flash(f"❌ Error adding certification: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.user_dashboard'))

    return render_template('add_certification.html')


@auth.route('/delete-education/<int:education_id>', methods=['POST'])
def delete_education(education_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        current_app.logger.warning('CSRF validation failed on delete_education')
        flash("❌ Invalid request", "error")
        return redirect(url_for('auth.user_dashboard'))
    success, msg = delete_user_item('education', 'education_id', education_id, session['user_id'])
    flash("✅ Education removed" if success else f"❌ {msg}", "success" if success else "error")
    return redirect(url_for('auth.user_dashboard'))


@auth.route('/delete-experience/<int:experience_id>', methods=['POST'])
def delete_experience(experience_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        current_app.logger.warning('CSRF validation failed on delete_experience')
        flash("❌ Invalid request", "error")
        return redirect(url_for('auth.user_dashboard'))
    success, msg = delete_user_item('experience', 'experience_id', experience_id, session['user_id'])
    flash("✅ Experience removed" if success else f"❌ {msg}", "success" if success else "error")
    return redirect(url_for('auth.user_dashboard'))


@auth.route('/delete-project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        current_app.logger.warning('CSRF validation failed on delete_project')
        flash("❌ Invalid request", "error")
        return redirect(url_for('auth.user_dashboard'))
    success, msg = delete_user_item('projects', 'project_id', project_id, session['user_id'])
    flash("✅ Project removed" if success else f"❌ {msg}", "success" if success else "error")
    return redirect(url_for('auth.user_dashboard'))


@auth.route('/delete-certification/<int:certification_id>', methods=['POST'])
def delete_certification(certification_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        current_app.logger.warning('CSRF validation failed on delete_certification')
        flash("❌ Invalid request", "error")
        return redirect(url_for('auth.user_dashboard'))
    success, msg = delete_user_item('certifications', 'certification_id', certification_id, session['user_id'])
    flash("✅ Certification removed" if success else f"❌ {msg}", "success" if success else "error")
    return redirect(url_for('auth.user_dashboard'))


def get_progress_trends(user_id, days=30):
    """Calculate historical progress per skill over the past N days."""
    conn = get_db_connection()
    if not conn:
        return {}

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT skill_id, skill_name
            FROM skills
            WHERE user_id = %s
        """, (user_id,))
        skills = cursor.fetchall()

        trends = {}
        for skill in skills:
            skill_id = skill['skill_id']

            cursor.execute("""
                SELECT DATE(log_date) as date, SUM(hours_spent) as hours
                FROM skill_logs
                WHERE user_id = %s AND skill_id = %s
                  AND log_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(log_date)
                ORDER BY date
            """, (user_id, skill_id, days))

            logs = cursor.fetchall()
            if logs:
                trends[skill_id] = [
                    {'date': str(log['date']), 'hours': float(log['hours'])}
                    for log in logs
                ]

        return trends

    except Exception as e:
        current_app.logger.error(f"Error in get_progress_trends: {str(e)}")
        return {}

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def get_hours_by_skill(user_id, days=14):
    """Get total hours spent on each skill over the past N days."""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.skill_name, COALESCE(SUM(sl.hours_spent), 0) as total_hours
            FROM skills s
            LEFT JOIN skill_logs sl ON s.skill_id = sl.skill_id
                AND sl.user_id = %s
                AND sl.log_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            WHERE s.user_id = %s
            GROUP BY s.skill_id, s.skill_name
            ORDER BY total_hours DESC
        """, (user_id, days, user_id))

        hours_data = cursor.fetchall()
        return [
            {'skill_name': row['skill_name'], 'hours': float(row['total_hours'])}
            for row in hours_data
        ]

    except Exception as e:
        current_app.logger.error(f"Error in get_hours_by_skill: {str(e)}")
        return []

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def estimate_completion_time(user_id, skill_id):
    """Estimate days remaining until skill reaches 100% based on recent pace."""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT current_progress, target_hours
            FROM skills
            WHERE skill_id = %s AND user_id = %s
        """, (skill_id, user_id))

        skill = cursor.fetchone()
        if not skill:
            return None

        current_progress = skill['current_progress'] if skill['current_progress'] else 0
        target_hours = skill['target_hours'] if skill['target_hours'] else 100

        if current_progress >= 100:
            return {
                'days_remaining': 0,
                'avg_hours_per_day': 0,
                'completion_date': 'Completed',
                'pace': 'complete'
            }

        cursor.execute("""
            SELECT COALESCE(SUM(hours_spent), 0) as total_hours
            FROM skill_logs
            WHERE user_id = %s AND skill_id = %s
              AND log_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """, (user_id, skill_id))

        result = cursor.fetchone()
        hours_in_30_days = float(result['total_hours']) if result else 0.0
        avg_hours_per_day = hours_in_30_days / 30.0 if hours_in_30_days > 0 else 0.5

        cursor.execute("""
            SELECT COALESCE(SUM(hours_spent), 0) as total_completed
            FROM skill_logs
            WHERE user_id = %s AND skill_id = %s
        """, (user_id, skill_id))

        total_result = cursor.fetchone()
        completed_hours = float(total_result['total_completed']) if total_result else 0.0

        remaining_hours = max(0, target_hours - completed_hours)
        days_remaining = int(remaining_hours / avg_hours_per_day) if avg_hours_per_day > 0 else 999

        pace = 'fast' if avg_hours_per_day >= 3 else 'normal' if avg_hours_per_day >= 1.5 else 'slow'

        from datetime import timedelta
        completion_date = (datetime.now() + timedelta(days=days_remaining)).strftime('%b %d, %Y')

        return {
            'days_remaining': days_remaining,
            'avg_hours_per_day': round(avg_hours_per_day, 2),
            'completion_date': completion_date,
            'pace': pace,
            'remaining_hours': round(remaining_hours, 1),
            'completed_hours': round(completed_hours, 1)
        }

    except Exception as e:
        current_app.logger.error(f"Error in estimate_completion_time: {str(e)}")
        return None

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


@auth.route('/track-progress')
def track_progress():
    """View all skills with progress tracking with trends and completion estimates"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()

    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT skill_id, skill_name, description, current_progress, target_hours, target_date
            FROM skills
            WHERE user_id = %s
            ORDER BY current_progress DESC
        """, (user_id,))
        skills = cursor.fetchall()

        # Fetch recent logs
        cursor.execute("""
            SELECT l.log_id, l.skill_id, s.skill_name, l.hours_spent, l.reflection_notes, l.log_date
            FROM skill_logs l
            JOIN skills s ON l.skill_id = s.skill_id
            WHERE s.user_id = %s
            ORDER BY l.log_date DESC
            LIMIT 10
        """, (user_id,))
        recent_logs = cursor.fetchall()

        beginner_skills = sum(1 for s in skills if (s['current_progress'] or 0) < 30)
        intermediate_skills = sum(1 for s in skills if 30 <= (s['current_progress'] or 0) < 70)
        advanced_skills = sum(1 for s in skills if (s['current_progress'] or 0) >= 70)

        trends = {}  # get_progress_trends(user_id, days=14)
        hours_by_skill = []  # get_hours_by_skill(user_id, days=14)
        progress_distribution = [beginner_skills, intermediate_skills, advanced_skills]

        return render_template(
            'track_progress.html',
            skills=skills,
            recent_logs=recent_logs,
            beginner_skills=beginner_skills,
            intermediate_skills=intermediate_skills,
            advanced_skills=advanced_skills,
            total_skills=len(skills),
            trends=trends,
            hours_by_skill=hours_by_skill,
            progress_distribution=progress_distribution
        )

    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.user_dashboard'))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


@auth.route('/update-progress/<int:skill_id>/<int:new_progress>')
def update_progress(skill_id, new_progress):
    """Quick update progress"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    if not is_valid_progress(new_progress):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Invalid progress value'})
        flash("❌ Invalid progress value", "error")
        return redirect(url_for('auth.track_progress'))

    user_id = session['user_id']
    conn = get_db_connection()

    if not conn:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Database error'})
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM skills WHERE skill_id=%s", (skill_id,))
        skill = cursor.fetchone()

        if not skill or skill['user_id'] != user_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Unauthorized access'})
            flash("❌ Unauthorized access", "error")
            return redirect(url_for('auth.track_progress'))

        proficiency_level = calculate_proficiency_level(new_progress)
        status = 'Completed' if new_progress >= 100 else 'Active'
        cursor.execute("""
            UPDATE skills
            SET current_progress=%s, proficiency_level=%s, status=%s, updated_at=NOW()
            WHERE skill_id=%s
        """, (int(new_progress), proficiency_level, status, skill_id))

        conn.commit()
        flash("✅ Progress updated!", "success")

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)})
        flash(f"❌ Error: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('auth.track_progress'))


@auth.route('/generate-cv')
def generate_cv():
    """Generate CV based on skills and proficiency"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()

    if not conn:
        flash("❌ Database error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT email FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        cursor.execute("SELECT * FROM user_profile WHERE user_id=%s", (user_id,))
        profile = cursor.fetchone()

        cursor.execute("""
            SELECT skill_name, description, current_progress, COALESCE(priority, 'Medium') as priority
            FROM skills
            WHERE user_id = %s
        """, (user_id,))
        skills = cursor.fetchall()
        skills = merge_sort_skills(skills, key='current_progress', reverse=True)

        cursor.execute("""
            SELECT s.skill_name, COALESCE(SUM(l.hours_spent), 0) as total_hours
            FROM skills s
            LEFT JOIN skill_logs l ON s.skill_id = l.skill_id AND l.user_id = s.user_id
            WHERE s.user_id = %s
            GROUP BY s.skill_name
        """, (user_id,))
        skill_hours = cursor.fetchall()
        skill_hours_dict = {hour['skill_name']: hour['total_hours'] for hour in skill_hours}

        education = []
        try:
            cursor.execute("SELECT * FROM education WHERE user_id=%s ORDER BY start_year DESC", (user_id,))
            education = cursor.fetchall()
        except Exception:
            pass

        experience = []
        try:
            cursor.execute("SELECT * FROM experience WHERE user_id=%s ORDER BY start_date DESC", (user_id,))
            experience = cursor.fetchall()
        except Exception:
            pass

        projects = []
        try:
            cursor.execute("SELECT * FROM projects WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
            projects = cursor.fetchall()
        except Exception:
            pass

        certifications = []
        try:
            cursor.execute("SELECT * FROM certifications WHERE user_id=%s ORDER BY issue_date DESC", (user_id,))
            certifications = cursor.fetchall()
        except Exception:
            pass

        for exp in experience:
            if exp.get('start_date') and isinstance(exp['start_date'], str):
                try:
                    exp['start_date'] = datetime.strptime(exp['start_date'], '%Y-%m-%d').strftime('%B %Y')
                except Exception:
                    pass
            if exp.get('end_date') and isinstance(exp['end_date'], str):
                try:
                    exp['end_date'] = datetime.strptime(exp['end_date'], '%Y-%m-%d').strftime('%B %Y')
                except Exception:
                    pass

        for cert in certifications:
            if cert.get('issue_date') and isinstance(cert['issue_date'], str):
                try:
                    cert['issue_date'] = datetime.strptime(cert['issue_date'], '%Y-%m-%d').strftime('%B %Y')
                except Exception:
                    pass

        if skills:
            total_progress = sum(skill['current_progress'] for skill in skills)
            average_progress = round(total_progress / len(skills), 2)

            if average_progress >= 80:
                proficiency_level = "Advanced"
                proficiency_description = "Expert level proficiency with extensive knowledge"
            elif average_progress >= 50:
                proficiency_level = "Intermediate"
                proficiency_description = "Competent professional with solid understanding"
            else:
                proficiency_level = "Beginner"
                proficiency_description = "Foundation level with active learning"

            advanced_skills = [s for s in skills if s['current_progress'] >= 80]
            intermediate_skills = [s for s in skills if 50 <= s['current_progress'] < 80]
            beginner_skills = [s for s in skills if s['current_progress'] < 50]
        else:
            average_progress = 0
            proficiency_level = "No Skills"
            proficiency_description = "No skills tracked yet"
            advanced_skills = []
            intermediate_skills = []
            beginner_skills = []

    except Exception as e:
        print(f"CV Generation Error: {str(e)}")
        flash(f"❌ Error generating CV: {str(e)}", "error")
        return redirect(url_for('auth.user_dashboard'))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    return render_template(
        'cv.html',
        user_email=user['email'] if user else "N/A",
        profile=profile,
        skills=skills,
        skill_hours_dict=skill_hours_dict,
        education=education,
        experience=experience,
        projects=projects,
        certifications=certifications,
        average_progress=average_progress,
        proficiency_level=proficiency_level,
        proficiency_description=proficiency_description,
        advanced_skills=advanced_skills,
        intermediate_skills=intermediate_skills,
        beginner_skills=beginner_skills,
        total_skills=len(skills),
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M")
    )


# ======================== ALGORITHM INTEGRATION ROUTES ========================

@auth.route('/sorted-skills')
def sorted_skills():
    """Display skills sorted using MERGE SORT algorithm"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()

    if not conn:
        flash("❌ Database connection error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT skill_id as id, skill_name as name, current_progress as progress
            FROM skills
            WHERE user_id=%s
            ORDER BY created_at DESC
        """, (user_id,))

        skills = cursor.fetchall()

        if not skills:
            flash("📝 No skills found. Add a skill to see sorting in action!", "info")
            return redirect(url_for('auth.user_dashboard'))

        skills_list = [
            {'id': skill['id'], 'name': skill['name'], 'progress': skill['progress']}
            for skill in skills
        ]

        sorted_skills_list = merge_sort_skills(skills_list, key='progress', reverse=True)

        for idx, skill in enumerate(sorted_skills_list, 1):
            skill['rank'] = idx

        return render_template(
            'sorted_skills.html',
            sorted_skills=sorted_skills_list,
            total_skills=len(sorted_skills_list),
            algorithm_name='Merge Sort',
            algorithm_complexity='O(n log n)',
            description='Skills sorted by progress percentage (highest to lowest) using Divide & Conquer'
        )

    except Exception as e:
        print(f"Sorted Skills Error: {str(e)}")
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.user_dashboard'))

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


@auth.route('/skill-recommendations')
def skill_recommendations():
    """Display skill recommendations using GREEDY ALGORITHM"""
    if 'user_id' not in session:
        flash("❌ Please login first", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    conn = get_db_connection()

    if not conn:
        flash("❌ Database connection error", "error")
        return redirect(url_for('auth.user_dashboard'))

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                skill_id as id,
                skill_name as name,
                current_progress as progress,
                COALESCE(priority, 'medium') as priority
            FROM skills
            WHERE user_id=%s
            ORDER BY created_at DESC
        """, (user_id,))

        skills = cursor.fetchall()

        if not skills:
            flash("📝 No skills found. Add skills with priorities to get recommendations!", "info")
            return redirect(url_for('auth.user_dashboard'))

        skills_list = [
            {
                'id': skill['id'],
                'name': skill['name'],
                'progress': skill['progress'],
                'priority': skill.get('priority', 'medium').lower()
            }
            for skill in skills
        ]

        top_recommendations = get_top_skill_recommendations(skills_list, top_n=3)
        all_recommendations = get_top_skill_recommendations(skills_list, top_n=len(skills_list))

        return render_template(
            'skill_recommendations.html',
            top_recommendations=top_recommendations,
            all_recommendations=all_recommendations,
            total_skills=len(skills_list),
            algorithm_name='Greedy Algorithm',
            algorithm_complexity='O(n)',
            description='Recommendations based on progress improvement potential and priority level'
        )

    except Exception as e:
        print(f"Skill Recommendations Error: {str(e)}")
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for('auth.user_dashboard'))

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass