''' import os module '''
import os
import traceback
from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .utils import *
from . import tasks
from .serializers import DownloadFileSerializer, DownloadM3U8Video, DownloadVideo


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_file(request: HttpRequest) -> "JsonResponse":
    '''
    TODO: Add documentation
    '''

    try:
        if request.method == "POST":
            serializer = DownloadFileSerializer(data=request.data)
            if serializer.is_valid(raise_exception=False):
                if not request.user.username:
                    raise Exception("Can not extract username from token!")

                file_url = serializer.data["file_url"]

                filename_with_extension = file_url.split('/')[-1]
                filename_without_extension = os.path.splitext(
                    filename_with_extension)[0]

                # Var: dest_filename
                if serializer.data["dest_filename"] is None:
                    dest_filename = filename_with_extension
                else:
                    dest_filename = serializer.data["dest_filename"]

                # Var: dest_directory
                # Edit dest_directory if it needs
                if serializer.data["dest_directory"] is not None:
                    # Remove / from end of dest_directory in case it is there
                    dest_directory = f"{request.user.username}" + "/" + serializer.data["dest_directory"] if serializer.data["dest_directory"][-1] != "/" else (
                        serializer.data["dest_directory"])[:-1]

                    # Remove / from start of dest_directory in case it is there
                    dest_directory = f"{request.user.username}" + "/" + \
                        dest_directory if dest_directory[0] != "/" else dest_directory[1:]
                else:
                    dest_directory = f"{request.user.username}/download"

                remote_file_addr = f"{dest_directory}/{dest_filename}"

                # Create Task
                my_task = tasks.download_task.delay(file_url,
                                                    remote_file_addr,
                                                    user=request.user.username)
                return JsonResponse({"task_id": my_task.task_id}, status=200)
            else:
                return JsonResponse(serializer.errors, status=400)

    except Exception as error:
        response_data = {
            'error': 'Something bad happend :(, ' + str(error),
        }
        return JsonResponse(response_data, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_m3u8(request: HttpRequest) -> "JsonResponse":
    try:
        if request.method == "POST":
            serializer = DownloadM3U8Video(data=request.data)
            if serializer.is_valid(raise_exception=False):
                check_username_token_extraction(request)
    except:
        pass


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_video(request: HttpRequest) -> "JsonResponse":
    '''
    TODO: Add documentation
    '''
    try:
        if request.method == "POST":
            serializer = DownloadVideo(data=request.data)
            if serializer.is_valid(raise_exception=False):

                check_username_token_extraction(request)

                # TODO: Check if the url is invalid trough an exception
                video_url = serializer.data['video_url']

                if serializer.data['desire_format'] is None:
                    desire_format = video_url.split(".")[-1]
                else:
                    desire_format = serializer.data['desire_format']

                if serializer.data["subtitles"] is not None:
                    subtitles = serializer.data["subtitles"]
                else:
                    subtitles = []

                meta_data = {
                    "full_name": f"{serializer.data['video_name']} ({serializer.data['year']}) - {serializer.data['quality']} {serializer.data['codec']}",
                    "year": serializer.data["year"],
                    "quality": serializer.data["quality"],
                    "codec": serializer.data["codec"]
                }

                # TODO: if year is blank, then remote_dir has an empty parentheses
                if serializer.data["dest_dir"] is None:
                    remote_dir = f"{request.user.username}/video/{serializer.data['video_name']} ({meta_data['year']})"
                else:
                    remote_dir = f"{request.user.username}/{serializer.data['dest_dir']}"

                # Create Task
                my_task = tasks.download_video_task.delay(
                    video_url,
                    meta_data,
                    desire_format,
                    subtitles,
                    remote_dir,
                    request.user.username)

                return JsonResponse({"task_id": my_task.task_id}, status=200)
            else:
                return JsonResponse(serializer.errors, status=400)

    except Exception as error:
        response_data = {
            'error': 'Something bad happend :(, ' + str(error),

        }
        traceback.print_exc()
        return JsonResponse(response_data, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_m3u8_video(request: HttpRequest) -> "JsonResponse":
    '''
    TODO: Add documentation
    '''
    try:
        if request.method == "POST":
            serializer = DownloadM3U8Video(data=request.data)
            if serializer.is_valid(raise_exception=False):
                check_username_token_extraction(request)

                # TODO: Check if the url is invalid trough an exception
                m3u8_url = serializer.data["m3u8_url"]

                if serializer.data["subtitles"] is not None:
                    subtitles = serializer.data["subtitles"]
                else:
                    subtitles = []

                meta_data = {
                    "full_name": f"{serializer.data['video_name']} ({serializer.data['year']}) - {serializer.data['quality']} {serializer.data['codec']}",
                    "year": serializer.data["year"],
                    "quality": serializer.data["quality"],
                    "codec": serializer.data["codec"]
                }

                # TODO: if year is blank, then remote_dir has an empty parentheses
                if serializer.data["dest_dir"] is None:
                    remote_dir = f"{request.user.username}/video/{serializer.data['video_name']} ({meta_data['year']})"
                else:
                    remote_dir = f"{request.user.username}/{serializer.data['dest_dir']}"


                # Create Task
                my_task = tasks.download_m3u8_video_task.delay(
                    m3u8_url,
                    serializer.data["stream_media"],
                    meta_data,
                    serializer.data['desire_format'],
                    subtitles,
                    remote_dir,
                    request.user.username)

                return JsonResponse({"task_id": my_task.task_id}, status=200)
            else:
                return JsonResponse(serializer.errors, status=400)

    except Exception as error:
        response_data = {
            'error': 'Something bad happend :(, ' + str(error),
        }
        return JsonResponse(response_data, status=500)
