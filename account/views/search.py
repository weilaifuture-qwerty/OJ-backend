from rest_framework.views import APIView
from rest_framework.response import Response
from account.models import User
from account.serializers import UserSerializer

class StudentSearchView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        students = User.objects.filter(
            username__icontains=query
        )[:20]  # Limit results
        return Response(UserSerializer(students, many=True).data) 