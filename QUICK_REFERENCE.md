# SkillTracker - Quick Reference Guide

## 🚀 START HERE

### Step 1: Start the Application
```bash
cd d:\Binda Shrestha\BCA\6th Sem\Project II\skilltracker
python start.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.10.198:5000
```

### Step 2: Open in Browser
- Go to: `http://localhost:5000`

### Step 3: Login
Use one of these accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@skilltracker.com | admin123 |
| Student | student@skilltracker.com | password123 |

---

## 📋 Complete Feature List

### User Dashboard Features
- ✅ Add skills with target hours
- ✅ Log learning hours
- ✅ Track progress with charts
- ✅ Edit and delete skills/logs
- ✅ View learning history

### Profile Management
- ✅ Edit personal profile
- ✅ Add education history
- ✅ Add work experience
- ✅ Add projects
- ✅ Add certifications
- ✅ Generate CV

### Algorithm Features
- ✅ Sorted Skills (Merge Sort algorithm)
- ✅ Skill Recommendations (Greedy algorithm)

### Admin Features
- ✅ Admin dashboard
- ✅ View all users
- ✅ Manage system

---

## 🔧 Maintenance Commands

### Reset Database
```bash
python reset_db.py
python fix_passwords.py
```

### Verify Routes
```bash
python diagnose_routes.py
```

### Stop Server
Press `CTRL+C` in terminal

---

## 📊 Database Structure

**10 Tables:**
1. roles - User roles (Admin, User)
2. users - User accounts
3. user_profile - Extended profile
4. skills - Skills being tracked
5. skill_logs - Learning hour logs
6. progress_log - Progress history
7. education - Education history
8. experience - Work experience
9. projects - Project portfolio
10. certifications - Certifications

---

## 🔐 Test Accounts

### Admin Account
```
Email: admin@skilltracker.com
Password: admin123
Access: /admin/dashboard
```

### Student Account
```
Email: student@skilltracker.com
Password: password123
Access: /user/dashboard
```

---

## 📍 Main URLs

| Feature | URL |
|---------|-----|
| Home | http://localhost:5000 |
| Login | http://localhost:5000/login |
| Register | http://localhost:5000/register |
| Dashboard (User) | http://localhost:5000/user/dashboard |
| Dashboard (Admin) | http://localhost:5000/admin/dashboard |
| Add Skill | http://localhost:5000/add-skill |
| View Logs | http://localhost:5000/view-logs |
| Track Progress | http://localhost:5000/track-progress |
| Generate CV | http://localhost:5000/generate-cv |
| Sorted Skills | http://localhost:5000/sorted-skills |
| Recommendations | http://localhost:5000/skill-recommendations |

---

## 🛠️ Troubleshooting

### Issue: "Can't connect to server"
**Solution:** Make sure MySQL is running
```bash
# Check MySQL service
mysql -u root -p

# If you get password prompt, MySQL is running
```

### Issue: "Database not found"
**Solution:** Run reset_db.py
```bash
python reset_db.py
```

### Issue: "Login fails"
**Solution:** Fix passwords
```bash
python fix_passwords.py
```

### Issue: "Routes not working"
**Solution:** Verify routes
```bash
python diagnose_routes.py
```

---

## 📁 Project Files

```
skilltracker/
├── app.py                    ✅ Main Flask app
├── algorithms.py             ✅ Merge Sort & Greedy
├── routes/auth.py            ✅ All routes (2300+ lines)
├── templates/                ✅ 20 HTML templates
├── static/                   ✅ CSS & images

Configuration:
├── .env                      ✅ Environment variables
├── requirements.txt          ✅ Python packages
├── database_schema.sql       ✅ Database schema

Utilities:
├── start.py                  ✅ Start application
├── reset_db.py               ✅ Reset database
├── fix_passwords.py          ✅ Fix password hashes
├── diagnose_routes.py        ✅ Verify routes

Documentation:
├── FINAL_STATUS_REPORT.md    ✅ Complete status
├── ALL_FIXES_DOCUMENTATION.md ✅ What was fixed
├── QUICK_REFERENCE.md        ✅ This file
```

---

## ✅ Verification Checklist

Before submitting, verify:

- [ ] Application starts: `python start.py`
- [ ] Login works with student account
- [ ] Login works with admin account
- [ ] Dashboard loads successfully
- [ ] Can add a skill
- [ ] Can view skills
- [ ] Can add a log
- [ ] Can view logs
- [ ] Track progress page loads
- [ ] Generate CV works
- [ ] Sorted Skills (Merge Sort) works
- [ ] Skill Recommendations (Greedy) works
- [ ] All 12 main routes accessible
- [ ] Profile editing works
- [ ] Delete operations work

---

## 📞 Quick Help

**Question:** How do I start the app?
**Answer:** `python start.py` then go to http://localhost:5000

**Question:** What are the test credentials?
**Answer:** 
- User: student@skilltracker.com / password123
- Admin: admin@skilltracker.com / admin123

**Question:** How do I reset the database?
**Answer:** `python reset_db.py` then `python fix_passwords.py`

**Question:** How do I verify everything is working?
**Answer:** `python diagnose_routes.py`

**Question:** Where are the templates?
**Answer:** `skilltracker/templates/` (20 files)

**Question:** How do I stop the server?
**Answer:** Press `CTRL+C` in the terminal

---

## 🎯 What Was Fixed

1. ✅ Added 4 missing database tables
2. ✅ Fixed Flask app startup
3. ✅ Corrected password hashing
4. ✅ Fixed form field mapping
5. ✅ Fixed syntax errors in delete routes
6. ✅ Created database reset utility
7. ✅ Created route diagnostic tool

---

## 📈 Current Status

```
✅ APPLICATION FULLY OPERATIONAL
✅ All 30 routes working
✅ All 20 templates present
✅ All database tables created
✅ Both test accounts functional
✅ All algorithms implemented
✅ Authentication working
✅ Session management working
```

---

## 🎓 Learning Outcomes

This project demonstrates:
- ✅ Flask web framework
- ✅ Database design (MySQL)
- ✅ Authentication & security
- ✅ CRUD operations
- ✅ Algorithm implementation (Merge Sort, Greedy)
- ✅ Session management
- ✅ User role management
- ✅ CSV export
- ✅ Dynamic content generation (CV)

---

**Ready to use! Start with: `python start.py`**
