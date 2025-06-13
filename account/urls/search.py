from django.urls import path
from .views.search import StudentSearchView

urlpatterns = [
    path('students/search/', StudentSearchView.as_view(), name='student-search'),
] 