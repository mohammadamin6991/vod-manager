import json
from django.http import HttpResponse
from django.http import JsonResponse
from . import tasks
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from .serializers import M3U8Serializer
from rest_framework.permissions import IsAuthenticated

# https://dev.to/alexmercedcoder/creating-a-restful-api-with-django-without-djangorestframework-17n7

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def m3u8(request):

    try:
        if request.method == "POST":
            serializer = M3U8Serializer(data=request.data)
            if serializer.is_valid(raise_exception=False):
                if not request.user.username:
                    raise Exception("Can not extract username from token!")
                my_task = tasks.generate_m3u8.delay(video_url=serializer.data["video_url"], user_maxq=serializer.data["maxq"], user=request.user.username)
                return JsonResponse({"task_id": my_task.task_id}, status=200)
            else:
                return JsonResponse(serializer.errors , status=400)


    except Exception as error:
        response_data = {
                            'error': 'Something bad happend :(, ' + str(error),
                        }
        return JsonResponse(response_data , status=500)