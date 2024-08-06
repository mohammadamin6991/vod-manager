from django.urls import path
from . import views


urlpatterns = [
    path('file', views.download_file, name="download_file"),
    path('m3u8_video', views.download_m3u8_video, name="download_m3u8_video"),
    path('video', views.download_video, name="download_video"),
]
