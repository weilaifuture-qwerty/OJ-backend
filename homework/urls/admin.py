from django.urls import re_path
from ..views.admin import (
    AdminStudentManagementAPI, AdminHomeworkDetailAPI,
    GradeHomeworkAPI, HomeworkStatisticsAPI, AdminUpdateHomeworkAPI
)

urlpatterns = [
    # Superadmin endpoints
    re_path(r"^admin_student_relation/?$", AdminStudentManagementAPI.as_view(), name="admin_student_relation"),
    
    # Additional admin endpoints
    re_path(r"^homework/(?P<homework_id>\d+)/?$", AdminUpdateHomeworkAPI.as_view(), name="admin_homework_update"),
    re_path(r"^homework_detail/?$", AdminHomeworkDetailAPI.as_view(), name="admin_homework_detail"),
    re_path(r"^grade_homework/?$", GradeHomeworkAPI.as_view(), name="grade_homework"),
    re_path(r"^homework_statistics/?$", HomeworkStatisticsAPI.as_view(), name="homework_statistics"),
]