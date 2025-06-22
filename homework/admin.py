from django.contrib import admin
from .models import (
    AdminStudentRelation, HomeworkAssignment, HomeworkProblem,
    StudentHomework, HomeworkSubmission, HomeworkComment
)


@admin.register(AdminStudentRelation)
class AdminStudentRelationAdmin(admin.ModelAdmin):
    list_display = ['admin', 'student', 'assigned_by', 'assigned_at', 'is_active']
    list_filter = ['is_active', 'assigned_at']
    search_fields = ['admin__username', 'student__username']


@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'due_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'due_date', 'created_at']
    search_fields = ['title', 'created_by__username']


@admin.register(HomeworkProblem)
class HomeworkProblemAdmin(admin.ModelAdmin):
    list_display = ['homework', 'problem', 'order', 'points', 'required']
    list_filter = ['required']
    ordering = ['homework', 'order']


@admin.register(StudentHomework)
class StudentHomeworkAdmin(admin.ModelAdmin):
    list_display = ['student', 'homework', 'status', 'grade_percent', 'assigned_at']
    list_filter = ['status', 'assigned_at']
    search_fields = ['student__username', 'homework__title']


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student_homework', 'problem', 'is_accepted', 'score', 'attempts', 'submitted_at']
    list_filter = ['is_accepted', 'submitted_at']


@admin.register(HomeworkComment)
class HomeworkCommentAdmin(admin.ModelAdmin):
    list_display = ['homework', 'author', 'created_at', 'is_pinned']
    list_filter = ['is_pinned', 'created_at']
    search_fields = ['author__username', 'content']