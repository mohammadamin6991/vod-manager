from django.shortcuts import render
from transcoder.celery import app
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated

# Reserved tasks are tasks that have been received, but are still waiting to be executed.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_reserved_tasks(request):
    if request.method == "GET":
        data = app.control.inspect().reserved()
        return JsonResponse(data, status=200, safe=False)


# You can get a list of tasks registered in the worker using the registered():
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_registered_tasks(request):
    if request.method == "GET":
        data = app.control.inspect().registered()
        return JsonResponse(data, status=200, safe=False)


#You can get a list of active tasks using active():
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_tasks(request):
    if request.method == "GET":
        data = app.control.inspect().active()
        return JsonResponse(data, status=200, safe=False)


#You can get a list of tasks waiting to be scheduled by using scheduled():
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_scheduled_tasks(request):
    if request.method == "GET":
        data = app.control.inspect().scheduled()
        return JsonResponse(data, status=200, safe=False)

#You can get a list of queues that a worker consumes from by using the active_queues control command:
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_queues(request):
    if request.method == "GET":
        data = app.control.inspect().active_queues()
        return JsonResponse(data, status=200, safe=False)
