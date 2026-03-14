# DJANGO MODULES
from django.contrib import admin
from django.urls import include, path

# THIRD PARTY MODULES
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Project urls
    path('admin/', admin.site.urls),
    path("", include("apps.users.urls")),
    path("blog/", include("apps.blogs.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
