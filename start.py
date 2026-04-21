#!/usr/bin/env python
"""
SkillTracker Application Launcher
Run this script to start the SkillTracker application.

Requirements:
- Python 3.7+
- MySQL server running
- .env file configured with DATABASE_* variables
- All dependencies installed: pip install -r requirements.txt

Usage:
    python start.py
    or
    python3 start.py
"""

import os
import sys

if __name__ == '__main__':
    try:
        from skilltracker.app import app
        app.run(debug=False, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print(f"❌ Make sure MySQL is running and .env is configured correctly")
        sys.exit(1)