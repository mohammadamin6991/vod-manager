from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated

from .serializers import UserSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated,])
def user_creation(request):
    return JsonResponse('{"status": "comming soon!"}', status=200)
    # serializer = UserSerializer(data=request.data)
    # if serializer.is_valid():
    #     serializer.save()
    #     print(serializer)
    #     return JsonResponse(serializer, status=status.HTTP_201_CREATED, safe=False)
    # else:
    #     return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
