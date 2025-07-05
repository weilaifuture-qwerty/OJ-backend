# Homework System API Endpoints Summary

## Fixed URL Structure

The homework system endpoints are now properly configured:

### Student Endpoints (at `/api/`):
- `GET /api/student_homework` - Get student's homework list
- `GET /api/student_homework_detail?id=<homework_id>` - Get homework detail
- `GET /api/homework_progress` - Get progress counts
- `POST /api/submit_homework_problem` - Submit problem solution
- `GET /api/homework_comments?homework_id=<id>` - Get comments
- `POST /api/homework_comments` - Create comment
- `DELETE /api/homework_comments?id=<comment_id>` - Delete comment

### Admin Endpoints (at `/api/`):
- `GET /api/admin_homework_list` - Get admin's homework list
- `POST /api/admin_create_homework` - Create new homework
- `DELETE /api/admin_delete_homework?id=<homework_id>` - Delete homework
- `GET /api/available_students` - Get available students

### Additional Admin Endpoints (at `/api/admin/`):
- `GET /api/admin/admin_list` - Get list of admins (for superadmin)
- `GET /api/admin/admin_student_relation` - Manage student assignments
- `GET /api/admin/homework_detail?id=<homework_id>` - Get detailed homework info
- `POST /api/admin/grade_homework` - Grade student homework
- `GET /api/admin/homework_statistics` - Get homework statistics

## Debug Endpoint
- `GET /api/homework_debug` - Verify homework system is working

## What Was Fixed

1. **URL Structure**: Moved admin endpoints that frontend expects at `/api/` level from `/api/admin/`
2. **Missing Endpoint**: Added `/api/admin/admin_list` to account app
3. **Import Issues**: Fixed circular imports and missing imports
4. **Query Issues**: Fixed aggregate queries using Sum() instead of F()

## Testing

To verify all endpoints are working:

```bash
# Test the debug endpoint
curl http://localhost:8000/api/homework_debug/

# Test admin list endpoint
curl -H "Cookie: <your-session-cookie>" http://localhost:8000/api/admin/admin_list/

# Test available students endpoint
curl -H "Cookie: <your-session-cookie>" http://localhost:8000/api/available_students/
```

## Frontend Integration

The frontend is now correctly integrated with these endpoints. The 404 errors should be resolved.