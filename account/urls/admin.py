from django.urls import re_path

from ..views.admin import UserAdminAPI, GenerateUserAPI, CreateUserAPI, SimpleCreateUserAPI

urlpatterns = [
    re_path(r"^user/?$", UserAdminAPI.as_view(), name="user_admin_api"),
    re_path(r"^generate_user/?$", GenerateUserAPI.as_view(), name="generate_user_api"),
    re_path(r"^create_user/?$", CreateUserAPI.as_view(), name="create_user_api"),
    re_path(r"^simple_create_user/?$", SimpleCreateUserAPI.as_view(), name="simple_create_user_api"),
]
