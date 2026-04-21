#!/usr/bin/env python
"""
Algorithm Testing Script
Tests the Merge Sort and Greedy Algorithm implementations
"""

import sys
import os

# Add the skilltracker directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skilltracker'))

def test_merge_sort():
    """Test the Merge Sort algorithm"""
    print("🧪 Testing Merge Sort Algorithm...")

    try:
        from skilltracker.algorithms import merge_sort_skills

        # Test data
        skills = [
            {'id': 1, 'name': 'Python', 'progress': 75},
            {'id': 2, 'name': 'JavaScript', 'progress': 90},
            {'id': 3, 'name': 'Java', 'progress': 60},
            {'id': 4, 'name': 'C++', 'progress': 85},
            {'id': 5, 'name': 'SQL', 'progress': 70}
        ]

        # Format skills for display
        original_display = [f"{s['name']}({s['progress']}%)" for s in skills]
        print(f"📊 Original skills: {original_display}")

        # Sort by progress (descending)
        sorted_skills = merge_sort_skills(skills, key='progress', reverse=True)

        # Format sorted skills for display
        sorted_display = [f"{s['name']}({s['progress']}%)" for s in sorted_skills]
        print(f"🔄 Sorted skills: {sorted_display}")

        # Verify sorting
        expected_order = ['JavaScript(90%)', 'C++(85%)', 'Python(75%)', 'SQL(70%)', 'Java(60%)']
        actual_order = [f"{s['name']}({s['progress']}%)" for s in sorted_skills]

        if actual_order == expected_order:
            print("✅ Merge Sort: PASSED")
            return True
        else:
            print("❌ Merge Sort: FAILED")
            print(f"Expected: {expected_order}")
            print(f"Actual: {actual_order}")
            return False

    except Exception as e:
        print(f"❌ Merge Sort Error: {e}")
        return False

def test_greedy_algorithm():
    """Test the Greedy Algorithm"""
    print("\n🧪 Testing Greedy Algorithm...")

    try:
        from skilltracker.algorithms import get_top_skill_recommendations

        # Test data
        skills = [
            {'id': 1, 'name': 'Python', 'progress': 75, 'priority': 'high'},
            {'id': 2, 'name': 'JavaScript', 'progress': 90, 'priority': 'medium'},
            {'id': 3, 'name': 'Java', 'progress': 60, 'priority': 'high'},
            {'id': 4, 'name': 'C++', 'progress': 85, 'priority': 'low'},
            {'id': 5, 'name': 'SQL', 'progress': 70, 'priority': 'medium'}
        ]

        print(f"📊 Skills data: {[(s['name'], s['progress'], s['priority']) for s in skills]}")

        # Get top 3 recommendations
        recommendations = get_top_skill_recommendations(skills, top_n=3)

        print(f"🎯 Top 3 recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['name']} (Score: {rec['recommendation_score']:.1f}, Progress: {rec['progress']}%, Priority: {rec['priority']})")

        # Verify we got 3 recommendations
        if len(recommendations) == 3:
            print("✅ Greedy Algorithm: PASSED (correct number of recommendations)")
            return True
        else:
            print(f"❌ Greedy Algorithm: FAILED (expected 3, got {len(recommendations)})")
            return False

    except Exception as e:
        print(f"❌ Greedy Algorithm Error: {e}")
        return False

def test_algorithm_imports():
    """Test that algorithms can be imported"""
    print("🧪 Testing Algorithm Imports...")

    try:
        from skilltracker.algorithms import merge_sort_skills, get_top_skill_recommendations, calculate_skill_priority_score
        print("✅ All algorithm imports: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

if __name__ == '__main__':
    print("🚀 SkillTracker Algorithm Testing Suite")
    print("=" * 50)

    # Test imports
    import_success = test_algorithm_imports()

    if not import_success:
        print("\n❌ Cannot proceed with tests due to import errors")
        sys.exit(1)

    # Test algorithms
    merge_sort_passed = test_merge_sort()
    greedy_passed = test_greedy_algorithm()

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"  Merge Sort: {'✅ PASSED' if merge_sort_passed else '❌ FAILED'}")
    print(f"  Greedy Algorithm: {'✅ PASSED' if greedy_passed else '❌ FAILED'}")

    if merge_sort_passed and greedy_passed:
        print("\n🎉 ALL TESTS PASSED! Algorithms are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! Please check the implementation.")
        sys.exit(1)