from django.urls import include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    re_path(r"^api/", include("account.urls.oj")),
    re_path(r"^api/admin/", include("account.urls.admin")),
    re_path(r"^api/", include("announcement.urls.oj")),
    re_path(r"^api/admin/", include("announcement.urls.admin")),
    re_path(r"^api/", include("conf.urls.oj")),
    re_path(r"^api/admin/", include("conf.urls.admin")),
    re_path(r"^api/", include("problem.urls.oj")),
    re_path(r"^api/admin/", include("problem.urls.admin")),
    re_path(r"^api/", include("contest.urls.oj")),
    re_path(r"^api/admin/", include("contest.urls.admin")),
    re_path(r"^api/", include("submission.urls.oj")),
    re_path(r"^api/admin/", include("submission.urls.admin")),
    re_path(r"^api/admin/", include("utils.urls")),
    re_path(r"^api/", include("homework.urls.oj")),
    re_path(r"^api/admin/", include("homework.urls.admin")),
]

# Serve avatar files in development
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^public/avatar/(?P<path>.*)$', serve, {'document_root': settings.AVATAR_UPLOAD_DIR}),
    ]
