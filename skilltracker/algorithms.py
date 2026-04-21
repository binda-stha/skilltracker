"""
Algorithm Implementation for SkillTracker
Contains: Merge Sort & Greedy Algorithm for skill management
"""

# ==================== MERGE SORT ALGORITHM ====================

def merge_sort_skills(skills, key='progress', reverse=True):
    """
    Merge Sort Algorithm - Sorts skills using Divide and Conquer approach
    
    Time Complexity: O(n log n) - Best, Average, and Worst case
    Space Complexity: O(n) - Additional space for merging
    
    Args:
        skills: List of dictionaries with skill data
        key: Key to sort by (default: 'progress')
        reverse: Sort in descending order if True (default: True)
    
    Returns:
        Sorted list of skill dictionaries
    
    Example:
        skills = [
            {"id": 1, "name": "Python", "progress": 70},
            {"id": 2, "name": "JavaScript", "progress": 45},
            {"id": 3, "name": "SQL", "progress": 90}
        ]
        sorted_skills = merge_sort_skills(skills)
        # Returns: [SQL(90), Python(70), JavaScript(45)]
    """
    
    # Base case: if list has 0 or 1 element, it's already sorted
    if len(skills) <= 1:
        return skills
    
    # Divide: Find the middle point
    mid = len(skills) // 2
    
    # Conquer: Recursively sort left and right halves
    left_half = merge_sort_skills(skills[:mid], key, reverse)
    right_half = merge_sort_skills(skills[mid:], key, reverse)
    
    # Combine: Merge the sorted halves
    return merge_skills(left_half, right_half, key, reverse)


def merge_skills(left, right, key='progress', reverse=True):
    """
    Merge two sorted lists of skill dictionaries
    
    Args:
        left: First sorted list
        right: Second sorted list
        key: Key to compare by
        reverse: Sort order (True = descending, False = ascending)
    
    Returns:
        Merged sorted list
    """
    
    result = []
    i = j = 0
    
    # Compare elements from left and right, add smaller/larger based on reverse
    while i < len(left) and j < len(right):
        left_value = left[i].get(key, 0)
        right_value = right[j].get(key, 0)
        
        # Determine comparison based on reverse flag
        if reverse:
            # Descending order: larger value first
            if left_value >= right_value:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        else:
            # Ascending order: smaller value first
            if left_value <= right_value:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
    
    # Add remaining elements from left
    result.extend(left[i:])
    
    # Add remaining elements from right
    result.extend(right[j:])
    
    return result


# ==================== GREEDY ALGORITHM ====================

def calculate_skill_priority_score(skills, priority_weights=None):
    """
    Greedy Algorithm - Calculate priority scores for skill recommendations
    
    Logic:
        score = (100 - progress) + priority_weight
        
    The algorithm greedily selects skills with highest scores
    (most improvement potential + highest priority)
    
    Time Complexity: O(n) - Single pass through all skills
    Space Complexity: O(n) - Store scores for each skill
    
    Args:
        skills: List of skill dictionaries with keys:
                - name (str): Skill name
                - progress (int): Current progress (0-100)
                - priority (str): 'high', 'medium', 'low'
        priority_weights: Dict mapping priority levels to weights
                         default: {'high': 30, 'medium': 20, 'low': 10}
    
    Returns:
        List of skills sorted by priority score (descending)
    
    Example:
        skills = [
            {"name": "Python", "progress": 70, "priority": "high"},
            {"name": "JavaScript", "progress": 45, "priority": "medium"},
            {"name": "SQL", "progress": 20, "priority": "low"}
        ]
        recommendations = calculate_skill_priority_score(skills)
    """
    
    # Default priority weights
    if priority_weights is None:
        priority_weights = {
            'high': 30,
            'medium': 20,
            'low': 10
        }
    
    # Step 1: Calculate score for each skill
    skills_with_scores = []
    
    for skill in skills:
        # Extract values with defaults
        progress = skill.get('progress', 0)
        priority = skill.get('priority', 'low').lower()
        
        # Get priority weight (default to 10 if invalid)
        priority_weight = priority_weights.get(priority, 10)
        
        # Greedy scoring: improvement potential + priority weight
        # Lower progress = higher improvement potential (100 - progress)
        score = (100 - progress) + priority_weight
        
        # Create new dict with score included
        skill_with_score = skill.copy()
        skill_with_score['recommendation_score'] = score
        
        skills_with_scores.append(skill_with_score)
    
    # Step 2: Sort by recommendation score (greedy selection)
    # Highest score first = highest priority recommendation
    sorted_recommendations = sorted(
        skills_with_scores,
        key=lambda x: x['recommendation_score'],
        reverse=True
    )
    
    return sorted_recommendations


def get_top_skill_recommendations(skills, top_n=3, priority_weights=None):
    """
    Get top N recommended skills to focus on
    
    Args:
        skills: List of skill dictionaries
        top_n: Number of top recommendations to return (default: 3)
        priority_weights: Custom priority weights
    
    Returns:
        List of top N recommended skills with scores
    """
    
    # Get all recommendations sorted by score
    all_recommendations = calculate_skill_priority_score(skills, priority_weights)
    
    # Return only top N
    return all_recommendations[:top_n]


# ==================== UTILITY FUNCTIONS ====================

def convert_priority_to_text(priority_level):
    """Convert priority level to readable text"""
    priority_map = {
        'high': '🔴 High Priority',
        'medium': '🟡 Medium Priority',
        'low': '🟢 Low Priority'
    }
    return priority_map.get(priority_level, 'Unknown')


def format_skill_output(skill, include_score=False):
    """Format skill dictionary for display"""
    output = {
        'id': skill.get('id', 'N/A'),
        'name': skill.get('name', 'Unknown'),
        'progress': skill.get('progress', 0),
        'priority': convert_priority_to_text(skill.get('priority', 'low'))
    }
    
    if include_score and 'recommendation_score' in skill:
        output['score'] = round(skill['recommendation_score'], 2)
    
    return output
