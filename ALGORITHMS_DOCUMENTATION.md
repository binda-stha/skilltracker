# Algorithm Implementation Guide - SkillTracker

## 📚 Table of Contents
1. [Merge Sort Algorithm](#merge-sort-algorithm)
2. [Greedy Algorithm](#greedy-algorithm)
3. [Implementation Details](#implementation-details)
4. [Integration with Flask](#integration-with-flask)
5. [Time Complexity Analysis](#time-complexity-analysis)
6. [Usage Examples](#usage-examples)

---

## 🔄 Merge Sort Algorithm

### Purpose
Sort skills by progress percentage (highest to lowest) using the **Divide and Conquer** approach.

### Algorithm Explanation

**Merge Sort** is a divide-and-conquer algorithm that works in three main steps:

#### 1. **Divide Phase**
- Split the unsorted list into two halves
- Recursively divide each half until you have single elements
- Single elements are considered sorted by definition

#### 2. **Conquer Phase**
- Each recursive call divides the problem into smaller subproblems
- Base case: A list of 1 element is already sorted

#### 3. **Merge Phase**
- Take two sorted sublists and merge them into one sorted list
- Compare elements from both lists and add the smaller/larger one to result
- Continue until all elements are processed

### Time Complexity Analysis

| Scenario | Complexity | Reason |
|----------|-----------|---------|
| **Best Case** | O(n log n) | Even if list is already sorted, algorithm still divides and merges |
| **Average Case** | O(n log n) | Consistent performance regardless of input distribution |
| **Worst Case** | O(n log n) | Guaranteed O(n log n) unlike quicksort |
| **Space Complexity** | O(n) | Need extra space for merging arrays |

### Why O(n log n)?
- **Division:** Splits the array in half recursively: log₂(n) levels deep
- **Merging:** Each merge operation takes O(n) time
- **Total:** log₂(n) levels × O(n) merge time = **O(n log n)**

### Visual Example

```
Original: [70, 45, 90, 30, 60]

DIVIDE:
        [70, 45, 90, 30, 60]
               ↙          ↘
         [70, 45]      [90, 30, 60]
          ↙    ↘      ↙      ↘
       [70]  [45]   [90]   [30, 60]
                              ↙   ↘
                           [30]  [60]

MERGE:
       [45, 70]      [30, 60, 90]
              ↘         ↙
                [30, 45, 60, 70, 90]
                (Then sort by progress in reverse)

RESULT: [90, 70, 60, 45, 30] (highest progress first)
```

### Code Implementation

```python
def merge_sort_skills(skills, key='progress', reverse=True):
    """
    Sort skills using Merge Sort Algorithm
    
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    
    # BASE CASE: Single element is already sorted
    if len(skills) <= 1:
        return skills
    
    # DIVIDE: Split list in half
    mid = len(skills) // 2
    left_half = skills[:mid]
    right_half = skills[mid:]
    
    # CONQUER: Recursively sort both halves
    left_sorted = merge_sort_skills(left_half, key, reverse)
    right_sorted = merge_sort_skills(right_half, key, reverse)
    
    # MERGE: Combine sorted halves
    return merge_skills(left_sorted, right_sorted, key, reverse)


def merge_skills(left, right, key='progress', reverse=True):
    """Merge two sorted lists"""
    result = []
    i = j = 0
    
    # Compare and merge
    while i < len(left) and j < len(right):
        left_val = left[i].get(key, 0)
        right_val = right[j].get(key, 0)
        
        if reverse:
            if left_val >= right_val:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        else:
            if left_val <= right_val:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
    
    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result
```

### When to Use Merge Sort?
✅ **Use when:**
- Consistent O(n log n) performance is required
- Stability is important (maintains relative order of equal elements)
- Working with linked lists
- Need guaranteed performance

❌ **Don't use when:**
- Space efficiency is critical (uses O(n) extra space)
- In-place sorting is required
- Working with small datasets (quicksort is faster for small n)

---

## 🎯 Greedy Algorithm

### Purpose
Recommend which skills the user should focus on next by calculating priority scores.

### Algorithm Explanation

**Greedy Algorithm** makes locally optimal choices at each step, expecting to find a global optimum.

#### Scoring Formula:
```
recommendation_score = (100 - progress) + priority_weight

Where:
  - (100 - progress) = Improvement potential (how much left to complete)
  - priority_weight = User-assigned priority:
      • High = 30 points
      • Medium = 20 points
      • Low = 10 points
```

#### Algorithm Steps:

1. **Calculate Scores**
   - For each skill, compute: (100 - progress) + priority_weight
   - This measures both urgency (low progress) and importance (high priority)

2. **Sort by Score**
   - Arrange skills in descending order of score
   - Highest score = most important to focus on

3. **Select Top N**
   - Return top N recommendations (typically top 3)

4. **Recommend**
   - Present recommendations to user

### Why is it Greedy?

The algorithm is "greedy" because:
- At each step, it selects the skill with the **highest score**
- It makes **locally optimal** choices (highest score right now)
- It expects this to lead to **globally optimal** prioritization
- It doesn't reconsider past selections (typical greedy behavior)

### Time Complexity Analysis

| Operation | Complexity | Reason |
|-----------|-----------|---------|
| **Score Calculation** | O(n) | Single pass through all skills |
| **Sorting** | O(n log n) | Sort by scores (if using efficient sort) |
| **Select Top N** | O(n) | Simple slicing/loop |
| **Overall** | O(n log n) | Dominated by sorting step |
| **In Practice** | ~O(n) | Sorting is optimized, typically linear for small n |

> **Note:** If we only need top 3, we can optimize to O(n) using selection algorithm instead of full sort.

### Example Calculation

```
Skills Data:
┌─────────────┬──────────┬──────────┐
│ Skill Name  │ Progress │ Priority │
├─────────────┼──────────┼──────────┤
│ Python      │ 70%      │ High     │
│ JavaScript  │ 45%      │ Medium   │
│ SQL         │ 20%      │ Low      │
│ DevOps      │ 30%      │ High     │
└─────────────┴──────────┴──────────┘

Step 1: Calculate Scores
  Python:      (100 - 70) + 30 = 60
  JavaScript:  (100 - 45) + 20 = 75  ← Highest Score
  SQL:         (100 - 20) + 10 = 90  ← HIGHEST Score
  DevOps:      (100 - 30) + 30 = 100 ← HIGHEST Score!

Step 2: Sort by Score (Descending)
  1. DevOps: 100    ← Focus here first!
  2. SQL: 90        ← Then here
  3. JavaScript: 75 ← Then here
  4. Python: 60     ← Last

Step 3: Top 3 Recommendations
  ✅ DevOps (100)
  ✅ SQL (90)
  ✅ JavaScript (75)

Insight:
  - DevOps has HIGH priority + low progress (30%) = HIGHEST recommendation
  - SQL has LOW priority but VERY low progress (20%) = SECOND recommendation
  - JavaScript has MEDIUM priority + medium progress = THIRD recommendation
  - Python has HIGH priority but HIGH progress (70%) = Least urgent
```

### Code Implementation

```python
def calculate_skill_priority_score(skills, priority_weights=None):
    """
    Greedy Algorithm: Calculate priority scores
    
    Time Complexity: O(n log n) [due to sorting]
    Space Complexity: O(n)
    """
    
    # Default priority weights
    if priority_weights is None:
        priority_weights = {
            'high': 30,
            'medium': 20,
            'low': 10
        }
    
    # STEP 1: Calculate scores for each skill (O(n))
    skills_with_scores = []
    
    for skill in skills:
        progress = skill.get('progress', 0)
        priority = skill.get('priority', 'low').lower()
        priority_weight = priority_weights.get(priority, 10)
        
        # Greedy Score: improvement potential + priority weight
        score = (100 - progress) + priority_weight
        
        skill_with_score = skill.copy()
        skill_with_score['recommendation_score'] = score
        skills_with_scores.append(skill_with_score)
    
    # STEP 2: Sort by score (greedy selection) - O(n log n)
    sorted_recommendations = sorted(
        skills_with_scores,
        key=lambda x: x['recommendation_score'],
        reverse=True
    )
    
    return sorted_recommendations


def get_top_skill_recommendations(skills, top_n=3):
    """Get top N recommendations"""
    all_recommendations = calculate_skill_priority_score(skills)
    return all_recommendations[:top_n]
```

### When to Use Greedy Algorithm?

✅ **Use when:**
- Need quick recommendations without complex optimization
- Local optimization likely leads to good global solution
- Performance is important (O(n) or O(n log n))
- Simple, interpretable logic is desired

❌ **Don't use when:**
- Guaranteed optimal solution is required
- Need to consider all possible combinations
- Problem requires backtracking or dynamic programming

### Advantages of Greedy for Skill Recommendations

1. **Fast:** O(n log n) vs O(2^n) for brute force
2. **Simple:** Easy to understand and explain to users
3. **Practical:** Works well for real-world prioritization
4. **Transparent:** Users see exactly how scores are calculated

---

## 🔧 Implementation Details

### File Structure

```
skilltracker/
├── algorithms.py              ← Algorithm implementations
├── routes/
│   └── auth.py               ← Flask routes using algorithms
└── templates/
    ├── sorted_skills.html    ← Merge Sort display
    └── skill_recommendations.html ← Greedy display
```

### Data Flow

```
DATABASE
    ↓
[Fetch skills as dictionaries]
    ↓
[Convert to Python list]
    ↓
[Pass to algorithm function]
    ↓
[Algorithm processes (O(n log n))]
    ↓
[Return sorted/recommended list]
    ↓
[Render in Flask template]
    ↓
USER INTERFACE
```

---

## 🚀 Integration with Flask

### Route 1: Sorted Skills (Merge Sort)

```python
@auth.route('/sorted-skills')
def sorted_skills():
    """Display skills sorted by progress using Merge Sort"""
    
    # 1. Validate session
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # 2. Fetch from database
    user_id = session['user_id']
    cursor.execute("""
        SELECT skill_id, skill_name, current_progress
        FROM skills WHERE user_id=%s
    """, (user_id,))
    skills = cursor.fetchall()
    
    # 3. Convert to list of dicts
    skills_list = [
        {'id': s['skill_id'], 'name': s['skill_name'], 'progress': s['current_progress']}
        for s in skills
    ]
    
    # 4. Apply algorithm
    sorted_skills = merge_sort_skills(skills_list, key='progress', reverse=True)
    
    # 5. Render template
    return render_template('sorted_skills.html', sorted_skills=sorted_skills)
```

### Route 2: Skill Recommendations (Greedy)

```python
@auth.route('/skill-recommendations')
def skill_recommendations():
    """Display recommendations using Greedy Algorithm"""
    
    # 1. Validate session
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # 2. Fetch from database
    user_id = session['user_id']
    cursor.execute("""
        SELECT skill_id, skill_name, current_progress, priority
        FROM skills WHERE user_id=%s
    """, (user_id,))
    skills = cursor.fetchall()
    
    # 3. Convert to list of dicts
    skills_list = [
        {
            'id': s['skill_id'],
            'name': s['skill_name'],
            'progress': s['current_progress'],
            'priority': s.get('priority', 'medium')
        }
        for s in skills
    ]
    
    # 4. Apply algorithm
    recommendations = get_top_skill_recommendations(skills_list, top_n=3)
    
    # 5. Render template
    return render_template('skill_recommendations.html', recommendations=recommendations)
```

---

## 📊 Time Complexity Analysis

### Comparison Table

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| **Merge Sort** | O(n log n) | O(n log n) | O(n log n) | O(n) | ✅ Yes |
| **Quick Sort** | O(n log n) | O(n log n) | O(n²) | O(log n) | ❌ No |
| **Bubble Sort** | O(n) | O(n²) | O(n²) | O(1) | ✅ Yes |
| **Greedy Rec.** | O(n) | O(n log n) | O(n log n) | O(n) | - |

### Why Merge Sort for Skills?

1. **Guaranteed O(n log n)** - Perfect for consistent performance
2. **Stable** - Preserves order of equal-progress skills
3. **Predictable** - No worst-case degradation like quicksort
4. **Suitable for lists** - Works well with Python lists

### Why Greedy for Recommendations?

1. **Linear time** - Simple calculation phase is O(n)
2. **Efficient** - Usually faster than optimal solutions
3. **Practical** - Works well in real scenarios
4. **Transparent** - Easy to explain to users

---

## 💻 Usage Examples

### Example 1: Using Merge Sort

```python
from skilltracker.algorithms import merge_sort_skills

# Sample skill data
skills = [
    {"id": 1, "name": "Python", "progress": 70},
    {"id": 2, "name": "JavaScript", "progress": 45},
    {"id": 3, "name": "SQL", "progress": 90},
    {"id": 4, "name": "React", "progress": 30}
]

# Sort by progress (highest first)
sorted_skills = merge_sort_skills(skills)

# Output:
# [
#   {"id": 3, "name": "SQL", "progress": 90},
#   {"id": 1, "name": "Python", "progress": 70},
#   {"id": 2, "name": "JavaScript", "progress": 45},
#   {"id": 4, "name": "React", "progress": 30}
# ]
```

### Example 2: Using Greedy Algorithm

```python
from skilltracker.algorithms import get_top_skill_recommendations

# Skills with priorities
skills = [
    {"name": "Python", "progress": 80, "priority": "high"},
    {"name": "JavaScript", "progress": 45, "priority": "medium"},
    {"name": "SQL", "progress": 20, "priority": "low"},
    {"name": "DevOps", "progress": 30, "priority": "high"}
]

# Get top 3 recommendations
recommendations = get_top_skill_recommendations(skills, top_n=3)

# Output with scores:
# [
#   {"name": "DevOps", "progress": 30, "priority": "high", "recommendation_score": 100},
#   {"name": "SQL", "progress": 20, "priority": "low", "recommendation_score": 90},
#   {"name": "JavaScript", "progress": 45, "priority": "medium", "recommendation_score": 75}
# ]
```

### Example 3: Integration in Flask Template

```html
<!-- In sorted_skills.html -->
{% for skill in sorted_skills %}
    <div class="skill-card">
        <h5>{{ skill.name }}</h5>
        <p>Progress: {{ skill.progress }}%</p>
        <div class="progress-bar">
            <div style="width: {{ skill.progress }}%"></div>
        </div>
    </div>
{% endfor %}
```

---

## 🧪 Testing

### Test Case 1: Merge Sort

```python
def test_merge_sort_basic():
    skills = [
        {"id": 1, "name": "A", "progress": 30},
        {"id": 2, "name": "B", "progress": 50},
        {"id": 3, "name": "C", "progress": 20}
    ]
    
    result = merge_sort_skills(skills)
    
    assert result[0]['progress'] == 50
    assert result[1]['progress'] == 30
    assert result[2]['progress'] == 20
    print("✅ Merge Sort Test Passed")
```

### Test Case 2: Greedy Algorithm

```python
def test_greedy_recommendations():
    skills = [
        {"name": "Python", "progress": 70, "priority": "high"},
        {"name": "JavaScript", "progress": 45, "priority": "medium"},
        {"name": "SQL", "progress": 20, "priority": "low"}
    ]
    
    recommendations = get_top_skill_recommendations(skills, top_n=1)
    
    # SQL should be first: (100-20) + 10 = 90
    assert recommendations[0]['name'] == 'SQL'
    assert recommendations[0]['recommendation_score'] == 90
    print("✅ Greedy Algorithm Test Passed")
```

---

## 🎓 Educational Value

### Concepts Covered:
- ✅ **Divide and Conquer** - Merge Sort
- ✅ **Greedy Algorithms** - Optimal substructure
- ✅ **Time Complexity** - Big-O analysis
- ✅ **Space Complexity** - Memory efficiency
- ✅ **Algorithm selection** - Choosing right algorithm
- ✅ **Real-world application** - Education/skill tracking

### Learning Outcomes:
- Understand how divide and conquer works
- Apply algorithms to practical problems
- Analyze algorithm efficiency
- Choose appropriate algorithms for different scenarios

---

## 🔗 Quick Links

- **Algorithm File:** `skilltracker/algorithms.py`
- **Flask Routes:** `skilltracker/routes/auth.py`
- **Sorted Skills Page:** `/sorted-skills`
- **Recommendations Page:** `/skill-recommendations`

---

**Created:** April 18, 2026  
**Project:** SkillTracker - BCA 6th Semester Project II  
**Status:** ✅ Production Ready
