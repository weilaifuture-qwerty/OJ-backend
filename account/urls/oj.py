from django.urls import re_path

from ..views.oj import (ApplyResetPasswordAPI, ResetPasswordAPI,
                        UserChangePasswordAPI, UserRegisterAPI, UserChangeEmailAPI,
                        UserLoginAPI, UserLogoutAPI, UsernameOrEmailCheck,
                        AvatarUploadAPI, TwoFactorAuthAPI, UserProfileAPI,
                        UserRankAPI, CheckTFARequiredAPI, SessionManagementAPI,
                        ProfileProblemDisplayIDRefreshAPI, OpenAPIAppkeyAPI, SSOAPI,
                        UserStreakAPI, DailyCheckInAPI, CheckAuthAPI, UserAvatarAPI,
                        UserStatusAPI)
from ..views.ai_suggestions import ProblemSuggestionsAPI, UserPracticeHistoryAPI
from ..views import get_csrf_token

from utils.captcha.views import CaptchaAPIView

urlpatterns = [
    re_path(r"^csrf/?$", get_csrf_token, name="get_csrf_token"),
    re_path(r"^login/?$", UserLoginAPI.as_view(), name="user_login_api"),
    re_path(r"^logout/?$", UserLogoutAPI.as_view(), name="user_logout_api"),
    re_path(r"^register/?$", UserRegisterAPI.as_view(), name="user_register_api"),
    re_path(r"^change_password/?$", UserChangePasswordAPI.as_view(), name="user_change_password_api"),
    re_path(r"^change_email/?$", UserChangeEmailAPI.as_view(), name="user_change_email_api"),
    re_path(r"^apply_reset_password/?$", ApplyResetPasswordAPI.as_view(), name="apply_reset_password_api"),
    re_path(r"^reset_password/?$", ResetPasswordAPI.as_view(), name="reset_password_api"),
    re_path(r"^captcha/?$", CaptchaAPIView.as_view(), name="show_captcha"),
    re_path(r"^check_username_or_email", UsernameOrEmailCheck.as_view(), name="check_username_or_email"),
    re_path(r"^profile/?$", UserProfileAPI.as_view(), name="user_profile_api"),
    re_path(r"^profile/fresh_display_id", ProfileProblemDisplayIDRefreshAPI.as_view(), name="display_id_fresh"),
    re_path(r"^upload_avatar/?$", AvatarUploadAPI.as_view(), name="avatar_upload_api"),
    re_path(r"^tfa_required/?$", CheckTFARequiredAPI.as_view(), name="tfa_required_check"),
    re_path(r"^two_factor_auth/?$", TwoFactorAuthAPI.as_view(), name="two_factor_auth_api"),
    re_path(r"^user_rank/?$", UserRankAPI.as_view(), name="user_rank_api"),
    re_path(r"^sessions/?$", SessionManagementAPI.as_view(), name="session_management_api"),
    re_path(r"^open_api_appkey/?$", OpenAPIAppkeyAPI.as_view(), name="open_api_appkey_api"),
    re_path(r"^sso?$", SSOAPI.as_view(), name="sso_api"),
    re_path(r"^user_streak/?$", UserStreakAPI.as_view(), name="user_streak_api"),
    re_path(r"^daily_check_in/?$", DailyCheckInAPI.as_view(), name="daily_check_in_api"),
    re_path(r"^check_auth/?$", CheckAuthAPI.as_view(), name="check_auth_api"),
    re_path(r"^problem_suggestions/?$", ProblemSuggestionsAPI.as_view(), name="problem_suggestions_api"),
    re_path(r"^user_practice_history/?$", UserPracticeHistoryAPI.as_view(), name="user_practice_history_api"),
    re_path(r"^user_avatar/?$", UserAvatarAPI.as_view(), name="user_avatar_api"),
    re_path(r"^user_status/?$", UserStatusAPI.as_view(), name="user_status_api")
]
