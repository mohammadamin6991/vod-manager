from unicodedata import name
from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('reserved/', views.get_reserved_tasks, name="reserved_url"),
    path('registered/', views.get_registered_tasks, name="registered_url"),
    path('active/', views.get_active_tasks, name="active_url"),
    path('scheduled/', views.get_scheduled_tasks, name="scheduled_url"),
    path('active-queues/', views.get_active_queues, name="active_queues_url"),
]


