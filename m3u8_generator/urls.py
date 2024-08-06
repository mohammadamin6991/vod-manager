from unicodedata import name
from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.m3u8, name="m3u8_generator_url"),
]
