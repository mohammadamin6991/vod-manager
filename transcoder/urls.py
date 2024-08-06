from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from users.views import user_creation

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/m3u8/', include("m3u8_generator.urls"),
         name="m3u8_generator_urls"),
    path('api/v1/download/', include("downloader.urls"), name="downloader_urls"),
    path("api/v1/celery-progress/",
         include("celery_progress.urls"), name="c_progress_urls"),
    path("api/v1/stats/", include("stats.urls"), name="stats_urls"),

    path("api/v1/auth/register/", user_creation, name="register_urls"),
    path('api/v1/auth/login/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
