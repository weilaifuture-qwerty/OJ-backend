from django.urls import re_path
from ..views.oj import (
    StudentHomeworkListAPI, StudentHomeworkDetailAPI,
    SubmitHomeworkProblemAPI, HomeworkProgressCountsAPI,
    HomeworkCommentsAPI, HomeworkSubmitProblemAPI,
    HomeworkSubmissionsListAPI
)
from ..views.admin import (
    AdminHomeworkListAPI, AdminCreateHomeworkAPI,
    AdminDeleteHomeworkAPI, AvailableStudentsAPI
)
from ..views.debug import DebugHomeworkAPI

urlpatterns = [
    # Debug endpoint
    re_path(r"^homework_debug/?$", DebugHomeworkAPI.as_view(), name="homework_debug"),
    
    # Student endpoints
    re_path(r"^student_homework/?$", StudentHomeworkListAPI.as_view(), name="student_homework_list"),
    re_path(r"^homework/list/?$", StudentHomeworkListAPI.as_view(), name="homework_list"),  # Alias for /api/homework/list
    re_path(r"^student_homework_detail/?$", StudentHomeworkDetailAPI.as_view(), name="student_homework_detail"),
    re_path(r"^homework/(?P<homework_id>\d+)/?$", StudentHomeworkDetailAPI.as_view(), name="homework_detail"),  # RESTful endpoint
    re_path(r"^submit_homework_problem/?$", SubmitHomeworkProblemAPI.as_view(), name="submit_homework_problem"),
    re_path(r"^homework/(?P<hw_id>\d+)/submit/(?P<prob_id>\d+)/?$", HomeworkSubmitProblemAPI.as_view(), name="homework_submit_problem"),  # RESTful submit
    re_path(r"^homework/(?P<hw_id>\d+)/submissions/?$", HomeworkSubmissionsListAPI.as_view(), name="homework_submissions_list"),  # RESTful submissions list
    re_path(r"^homework_progress/?$", HomeworkProgressCountsAPI.as_view(), name="homework_progress"),
    re_path(r"^homework_comments/?$", HomeworkCommentsAPI.as_view(), name="homework_comments"),
    
    # Admin endpoints that should be at /api/ level (not /api/admin/)
    re_path(r"^admin_homework_list/?$", AdminHomeworkListAPI.as_view(), name="admin_homework_list"),
    re_path(r"^admin_create_homework/?$", AdminCreateHomeworkAPI.as_view(), name="admin_create_homework"),
    re_path(r"^admin_delete_homework/?$", AdminDeleteHomeworkAPI.as_view(), name="admin_delete_homework"),
    re_path(r"^available_students/?$", AvailableStudentsAPI.as_view(), name="available_students"),
]