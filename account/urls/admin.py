from django.conf.urls import url

from ..views.admin import UserAdminAPI, GenerateUserAPI, CreateUserAPI

urlpatterns = [
    url(r"^user/?$", UserAdminAPI.as_view(), name="user_admin_api"),
    url(r"^generate_user/?$", GenerateUserAPI.as_view(), name="generate_user_api"),
    url(r"^create_user/?$", CreateUserAPI.as_view(), name="create_user_api"),
]
