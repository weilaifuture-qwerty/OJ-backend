from django.urls import path
from .views import AssignTaskView, StudentSearchView

urlpatterns = [
    path('tasks/assign/', AssignTaskView.as_view(), name='assign-task'),
    path('students/search/', StudentSearchView.as_view(), name='student-search'),
] 