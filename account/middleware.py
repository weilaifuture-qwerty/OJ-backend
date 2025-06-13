from django.conf import settings
from django.db import connection
from django.utils.timezone import now
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
import logging

from utils.api import JSONResponse
from account.models import User

logger = logging.getLogger(__name__)


class APITokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        appkey = request.META.get("HTTP_APPKEY")
        if appkey:
            try:
                request.user = User.objects.get(open_api_appkey=appkey, open_api=True, is_disabled=False)
                request.csrf_processing_done = True
                request.auth_method = "api_key"
            except User.DoesNotExist:
                pass


class SessionRecordMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.ip = request.META.get(settings.IP_HEADER, request.META.get("REMOTE_ADDR"))
        if request.user.is_authenticated:
            session = request.session
            session["user_agent"] = request.META.get("HTTP_USER_AGENT", "")
            session["ip"] = request.ip
            session["last_activity"] = now()
            user_sessions = request.user.session_keys
            if session.session_key not in user_sessions:
                user_sessions.append(session.session_key)
                request.user.save()


class AdminRoleRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path_info
        if path.startswith("/admin/") or path.startswith("/api/admin/"):
            if not (request.user.is_authenticated and request.user.is_admin_role()):
                return JSONResponse.response({"error": "login-required", "data": "Please login in first"})


class LogSqlMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        print("\033[94m", "#" * 30, "\033[0m")
        time_threshold = 0.03
        for query in connection.queries:
            if float(query["time"]) > time_threshold:
                print("\033[93m", query, "\n", "-" * 30, "\033[0m")
            else:
                print(query, "\n", "-" * 30)
        return response


class TimezoneMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.debug(f"TimezoneMiddleware: Activating UTC timezone. Current timezone: {timezone.get_current_timezone_name()}")
        timezone.activate('UTC')
        logger.debug(f"TimezoneMiddleware: UTC timezone activated. New timezone: {timezone.get_current_timezone_name()}")
        
        # Set database timezone
        with connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC';")
            cursor.execute("SHOW timezone;")
            db_timezone = cursor.fetchone()[0]
            logger.debug(f"TimezoneMiddleware: Database timezone: {db_timezone}")
        
        return None

    def process_response(self, request, response):
        logger.debug(f"TimezoneMiddleware: Deactivating timezone. Current timezone: {timezone.get_current_timezone_name()}")
        timezone.deactivate()
        logger.debug(f"TimezoneMiddleware: Timezone deactivated. New timezone: {timezone.get_current_timezone_name()}")
        return response
