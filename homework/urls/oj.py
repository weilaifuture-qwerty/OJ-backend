from django.urls import re_path
from ..views.oj import (
    StudentHomeworkListAPI, StudentHomeworkDetailAPI,
    SubmitHomeworkProblemAPI, HomeworkProgressAPI,
    HomeworkCommentsAPI
)

urlpatterns = [
    # Student endpoints
    re_path(r"^student_homework/?$", StudentHomeworkListAPI.as_view(), name="student_homework_list"),
    re_path(r"^student_homework_detail/?$", StudentHomeworkDetailAPI.as_view(), name="student_homework_detail"),
    re_path(r"^submit_homework_problem/?$", SubmitHomeworkProblemAPI.as_view(), name="submit_homework_problem"),
    re_path(r"^homework_progress/?$", HomeworkProgressAPI.as_view(), name="homework_progress"),
    re_path(r"^homework_comments/?$", HomeworkCommentsAPI.as_view(), name="homework_comments"),
]