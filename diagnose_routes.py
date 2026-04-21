#!/usr/bin/env python3
"""
SkillTracker Route Diagnostic Script
Tests if all routes are properly registered and the app can start
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from skilltracker.app import app
    print("✅ Application loaded successfully")
    
    # Check if app has routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'rule': rule.rule,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'endpoint': rule.endpoint
        })
    
    print(f"\n✅ Found {len(routes)} routes:")
    print("="*70)
    
    # Sort by endpoint
    routes_sorted = sorted(routes, key=lambda x: x['endpoint'])
    
    for route in routes_sorted:
        print(f"  {route['endpoint']:30} {route['rule']:30} {route['methods']}")
    
    print("="*70)
    
    # Check auth routes specifically
    auth_routes = [r for r in routes if 'auth' in r['endpoint']]
    print(f"\n✅ Auth routes: {len(auth_routes)}")
    
    critical_routes = [
        'auth.login',
        'auth.register',
        'auth.logout',
        'auth.user_dashboard',
        'auth.add_skill',
        'auth.add_log',
        'auth.view_logs',
        'auth.track_progress',
        'auth.edit_profile',
        'auth.generate_cv',
        'auth.sorted_skills',
        'auth.skill_recommendations'
    ]
    
    print(f"\nChecking critical routes:")
    print("="*70)
    for cr in critical_routes:
        exists = any(r['endpoint'] == cr for r in routes)
        status = "✅" if exists else "❌"
        print(f"  {status} {cr}")
    
    missing = [cr for cr in critical_routes if not any(r['endpoint'] == cr for r in routes)]
    if missing:
        print(f"\n⚠️  Missing routes: {', '.join(missing)}")
    else:
        print(f"\n✅ All critical routes are registered!")
    
    # Check templates
    print(f"\n\nChecking templates:")
    print("="*70)
    templates_dir = Path(__file__).parent / 'skilltracker' / 'templates'
    if templates_dir.exists():
        templates = list(templates_dir.glob('*.html'))
        print(f"✅ Found {len(templates)} templates in {templates_dir}")
        for tmpl in sorted(templates):
            print(f"  - {tmpl.name}")
    else:
        print(f"❌ Templates directory not found: {templates_dir}")
    
    # Check static files
    print(f"\n\nChecking static files:")
    print("="*70)
    static_dir = Path(__file__).parent / 'skilltracker' / 'static'
    if static_dir.exists():
        static_files = list(static_dir.glob('*'))
        print(f"✅ Found {len(static_files)} static files in {static_dir}")
        for sf in sorted(static_files):
            print(f"  - {sf.name}")
    else:
        print(f"❌ Static directory not found: {static_dir}")
    
    print("\n" + "="*70)
    print("✅ DIAGNOSTIC COMPLETE - Application structure looks good!")
    print("="*70)
    
except ImportError as e:
    print(f"❌ Failed to import application: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during diagnostic: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
