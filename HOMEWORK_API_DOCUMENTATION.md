# Homework System API Documentation

## User/Student Management Endpoints

### 1. GET /api/users
Alternative endpoint for getting users/students with flexible filtering.

**Query Parameters:**
- `type` (optional): 'student', 'admin', or 'all' (default: 'student')
- `search` (optional): Search by username, email, or real name
- `group` (optional): Filter by student group/class
- `page` (optional): Enable pagination

**Response:**
```json
{
  "error": null,
  "data": [
    {
      "id": 1,
      "username": "student1",
      "email": "student1@example.com",
      "real_name": "John Doe",
      "admin_type": "Regular User",
      "is_disabled": false,
      "create_time": "2024-01-01T10:00:00Z",
      "school": "Example University",
      "major": "Computer Science",
      "student_group": "CS101",
      "accepted_number": 10,
      "submission_number": 50
    }
  ]
}
```

### 2. GET /api/students_by_group
Get students organized by their groups/classes.

**Response:**
```json
{
  "error": null,
  "data": {
    "groups": [
      {
        "name": "CS101",
        "students": [
          {
            "id": 1,
            "username": "student1",
            "email": "student1@example.com",
            "real_name": "John Doe",
            "student_group": "CS101"
          }
        ]
      },
      {
        "name": "Ungrouped",
        "students": [...]
      }
    ],
    "total_groups": 3,
    "total_students": 50,
    "ungrouped_count": 10
  }
}
```

### 3. GET /api/available_students (Enhanced)
Get students available for homework assignment with advanced filtering.

**Query Parameters:**
- `search` (optional): Search by username, email, or real name
- `group` (optional): Filter by student group
- `exclude_homework_id` (optional): Exclude students already assigned to this homework

**Response:**
```json
{
  "error": null,
  "data": [
    {
      "id": 1,
      "username": "student1",
      "email": "student1@example.com",
      "real_name": "John Doe",
      "student_group": "CS101",
      "total_homework": 5,
      "completed_homework": 3,
      "average_grade": 85.5
    }
  ]
}
```

### 4. POST /api/update_student_group
Update a student's group/class assignment.

**Request Body:**
```json
{
  "student_id": 1,
  "group_name": "CS102"
}
```

**Response:**
```json
{
  "error": null,
  "data": {
    "message": "Student group updated successfully",
    "student_id": 1,
    "group_name": "CS102"
  }
}
```

### 5. GET /api/available_groups
Get list of all available student groups.

**Response:**
```json
{
  "error": null,
  "data": {
    "groups": ["CS101", "CS102", "MATH201"],
    "count": 3
  }
}
```

### 6. GET /api/admin/admin_list
Get list of admin users (for superadmin).

**Response:**
```json
{
  "error": null,
  "data": [
    {
      "id": 2,
      "username": "admin1",
      "email": "admin1@example.com",
      "real_name": "Admin User",
      "admin_type": "Admin",
      "student_count": 25
    }
  ]
}
```

## Homework Assignment with Groups

### Example: Create Homework for Specific Group

```json
POST /api/admin_create_homework
{
  "title": "Week 1 Assignment",
  "description": "Basic programming problems",
  "due_date": "2024-07-01T23:59:59Z",
  "problem_ids": [1, 2, 3],
  "student_ids": [],  // Empty to use group assignment
  "auto_grade": true
}
```

Then assign to a group:
1. Get students from group: `GET /api/students_by_group`
2. Extract student IDs from the CS101 group
3. Update homework assignment with those student IDs

## Migration Required

To support the group functionality, run:

```bash
python manage.py makemigrations account
python manage.py migrate
```

This will add the `student_group` field to the UserProfile model.

## Frontend Integration

The frontend can now:
1. Use `/api/users` as an alternative to `/api/available_students`
2. Filter students by group using the `group` parameter
3. Display students organized by groups using `/api/students_by_group`
4. Update student groups dynamically
5. Get available groups for dropdown menus

## Permissions

- Regular admins can only see/manage their assigned students
- Super admins can see all students
- Group updates require admin privileges
- Students cannot modify their own group assignments