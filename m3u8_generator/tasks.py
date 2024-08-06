"""System module."""
import os
import shutil
import datetime
from time import sleep
from celery import shared_task
from celery_progress.backend import ProgressRecorder
import boto3
from downloader.tasks import download
from s3_handler import tasks as s3_task
from django.conf import settings
from . import ffmpeg_streaming
from botocore.errorfactory import ClientError
from .ffmpeg_streaming import Bitrate, Formats, Representation, Size
from .ffmpeg_streaming import FFProbe

def monitor(ffmpeg, duration, time_, time_left, process, monitor_args, **kargs):
    """ monitor status of process """

    if int(datetime.datetime.now().timestamp() * 10) % 2 == 0:
        task_id = monitor_args["task_id"]
        task = monitor_args["self"]
        meta={
            "pending": False,
            "current": time_,
            "total": duration,
            "speed": kargs["speed"],
            "percent": int((time_ / duration) * 100),
            "description": "2/4 Generating M3U8 from Video File"
        }
        print(kargs["speed"])
        task.update_state(task_id=task_id, state='TRANSCODING', meta=meta)



@shared_task(bind=True)
def generate_m3u8(self, video_url, user_maxq, user="global",):
    """
    generate m3u8

    """
    try:
        progress_recorder = ProgressRecorder(self)
        progress_recorder.set_progress(0, 100, "1/4 Download Video File")
        task_id = self.request.id


        filename_with_extension = video_url.split('/')[-1]
        filename_without_extension = os.path.splitext(filename_with_extension)[0]

        temp_download_directory = settings.TEMP_DOWNLOAD_DIR

        # should not end with / (when we use it, we add / and if we add this here it create a folder name / in video directory !!!)
        remote_folder = f"{user}"

        hls_output_folder = f"{temp_download_directory}/{filename_without_extension}_m3u8/"


        progress_description = "1/4 Download Video File"
        # Download URL and store it locally
        download(video_url, progress_recorder, progress_description, split_by = 20)

        progress_recorder.set_progress(0, 100, "2/4 Generating M3U8 from Video File")



        # HLS Settings
        video = ffmpeg_streaming.input(f"{temp_download_directory}{filename_with_extension}")
        ffprobe = FFProbe(f"{temp_download_directory}{filename_with_extension}")

        first_video = ffprobe.streams().video()
        print(first_video)
        height = first_video.get('height', "Unknown")

        # Representations for generated playlist

        reps = {
            "360"   : Representation(Size(640, 360),
                                        Bitrate(1024 * 1024, 192 * 1024),
                                        maxrate=int(1.07 * 1024 * 1024),
                                        bufsize=int(1.5 * 1024 * 1024)),

            "480"   : Representation(Size(854, 480),
                                        Bitrate(2048 * 1024, 192 * 1024),
                                        maxrate=int(1.07 * 2048 * 1024),
                                        bufsize=int(1.5 * 2048 * 1024)),

            "720"   : Representation(Size(1280, 720),
                                        Bitrate(4096 * 1024, 320 * 1024),
                                        maxrate=int(1.07 * 4096 * 1024),
                                        bufsize=int(1.5 * 4096 * 1024)),

            "1080"  : Representation(Size(1920, 1080),
                                        Bitrate(8192 * 1024, 320 * 1024),
                                        maxrate=int(1.07 * 8192 * 1024),
                                        bufsize=int(1.5 * 8192 * 1024)),

            "1440"  : Representation(Size(2560, 1440),
                                        Bitrate(16384 * 1024, 320 * 1024),
                                        maxrate=int(1.07 * 16384 * 1024),
                                        bufsize=int(1.5 * 16384 * 1024)),

            "2160"  : Representation(Size(4096, 2160),
                                        Bitrate(32768 * 1024, 320 * 1024),
                                        maxrate=int(1.07 * 32768 * 1024),
                                        bufsize=int(1.5 * 32768 * 1024)),
        }

        # _1080p_60fps  = Representation(Size(1920, 1080),
        #                                    Bitrate(12288 * 1024, 320 * 1024),
        #                                    maxrate=int(1.07 * 12288 * 1024),
        #                                    bufsize=int(1.5 * 12288 * 1024))

        # _1440p_60fps  = Representation(Size(2560, 1440),
        #                                    Bitrate(24576 * 1024, 320 * 1024),
        #                                    maxrate=int(1.07 * 24576 * 1024),
        #                                    bufsize=int(1.5 * 24576 * 1024))

        # _2160p_60fps  = Representation(Size(4096, 2160),
        #                                    Bitrate(49152 * 1024, 320 * 1024),
        #                                    maxrate=int(1.07 * 49152 * 1024),
        #                                    bufsize=int(1.5 * 49152 * 1024))

        # _1440p_60fps_HDR  = Representation(Size(2560, 1440),
        #                                    Bitrate(32768 * 1024, 320 * 1024),
        #                                    maxrate=int(1.07 * 32768 * 1024),
        #                                    bufsize=int(1.5 * 32768 * 1024))


        # _2160p_60fps_HDR  = Representation(Size(4096, 2160),
        #                                    Bitrate(65536 * 1024, 320 * 1024),
        #                                    maxrate=int(1.07 * 65536 * 1024),
        #                                    bufsize=int(1.5 * 65536 * 1024))



        hls = video.hls(Formats.h264(),
                        keyint_min=48,
                        g=48,
                        sc_threshold=0,
                        hls_list_size=0,
                        hls_time=4,
                        hls_allow_cache=1,
                        sn=None)

        if user_maxq is not None:
            profile_list = []
            for rep_height, rep in reps.items():
                if int(rep_height) <= int(user_maxq):
                    profile_list.append(rep)
            profile = tuple(profile_list)

        elif height != "Unknown":
            profile_list = []
            for rep_height, rep in reps.items():
                if int(rep_height) <= int(height):
                    profile_list.append(rep)
            profile = tuple(profile_list)

        else:
            profile = (reps["360"], reps["480"], reps["720"], reps["1080"])

        hls.representations(*profile)

        monitor_args={
            "self": self,
            "task_id": task_id
            }


        hls.output(f"{hls_output_folder}/playlist.m3u8", monitor=monitor, monitor_args=monitor_args)


        # Upload Files to S3 Storage
        s3_storage = boto3.client('s3', aws_access_key_id=settings.S3_ACCESS_KEY,
                                        aws_secret_access_key=settings.S3_SECRET_KEY,
                                        region_name=settings.S3_REGION_NAME,
                                        endpoint_url=settings.S3_ENDPOINT_URL)


        try:
            s3_storage.head_object(Bucket="media-content",
                                   Key=f"{remote_folder}/video/{filename_without_extension}/{filename_with_extension}")
            progress_recorder.set_progress(100, 100, "3/4 File Already Uploaded")
            print("3/4 File Already Uploaded")
            sleep(5)
        except ClientError:
            # remote_folder should not ends with / becuase we add / after it here
            progress_recorder.set_progress(0, 100, "3/4 Upload Original File to S3")
            s3_task.upload_file(f"{temp_download_directory}{filename_with_extension}",
                                f"{remote_folder}/video/{filename_without_extension}/{filename_with_extension}",
                                "media-content",
                                s3_storage,
                                task_id,
                                self,
                                "3/4 Upload Original File to S3")

        progress_recorder.set_progress(0, 100, "4/4 Upload M3U8 Directory to S3")

        # remote_folder should not ends with / becuase we add / after it here
        s3_task.upload_files(hls_output_folder,
                            f"{remote_folder}/m3u8/{filename_without_extension}_m3u8/",
                            "media-content",
                            s3_storage,
                            progress_recorder,
                            "4/4 Upload M3U8 Directory to S3")

        return "Done"
    except Exception as error:
        print("\nError Occurred!! \n" + str(error))

    finally:
        for filename in os.listdir(temp_download_directory):
            file_path = os.path.join(temp_download_directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as error:
                print(f'Failed to delete {file_path}. Reason: {error}')
