from rest_framework.views import APIView
from rest_framework.response import Response
from classroom.models import Task
from account.models import User
from account.serializers import UserSerializer

class AssignTaskView(APIView):
    def post(self, request):
        student_ids = request.data.get('student_ids', [])
        task_id = request.data.get('task_id')
        task = Task.objects.get(id=task_id)
        students = User.objects.filter(id__in=student_ids)
        task.students.add(*students)
        return Response({'status': 'success'})

class StudentSearchView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        students = User.objects.filter(
            username__icontains=query
        )[:20]  # Limit results
        return Response(UserSerializer(students, many=True).data) 