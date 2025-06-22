from django.urls import re_path
from ..views.admin import (
    AdminStudentManagementAPI, AdminListAPI, HomeworkManagementAPI,
    HomeworkDetailAPI, AssignHomeworkToStudentsAPI, GradeHomeworkAPI,
    StudentListAPI
)

urlpatterns = [
    # Superadmin endpoints
    re_path(r"^admin_student_relation/?$", AdminStudentManagementAPI.as_view(), name="admin_student_relation"),
    re_path(r"^admin_list/?$", AdminListAPI.as_view(), name="admin_list"),
    
    # Admin homework management
    re_path(r"^homework/?$", HomeworkManagementAPI.as_view(), name="homework_management"),
    re_path(r"^homework_detail/?$", HomeworkDetailAPI.as_view(), name="homework_detail"),
    re_path(r"^assign_homework/?$", AssignHomeworkToStudentsAPI.as_view(), name="assign_homework"),
    re_path(r"^grade_homework/?$", GradeHomeworkAPI.as_view(), name="grade_homework"),
    re_path(r"^student_list/?$", StudentListAPI.as_view(), name="student_list"),
]