from .views import get_csrf_token

urlpatterns = [
    path('csrf/', get_csrf_token, name='get_csrf_token'),
] 