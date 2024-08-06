''' import os module '''
import os
import shutil
import boto3
from django.conf import settings
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from s3_handler import tasks as s3_task
from .utils import *


@shared_task(bind=True)
def download_task(self, file_url, remote_file_addr):
    '''
    download a file to s3
    '''
    try:
        progress_recorder = ProgressRecorder(self)
        progress_recorder.set_progress(0, 100, "1/2 Download Video File")
        task_id = self.request.id

        progress_description = "1/2 Download Video File"
        temp_download_directory = settings.TEMP_DOWNLOAD_DIR

        # Download URL and store it locally
        download(file_url, progress_recorder,
                 progress_description, split_by=20)

        filename_with_extension = file_url.split('/')[-1]

        # Upload Files to S3 Storage
        s3_storage = boto3.client('s3', aws_access_key_id=settings.S3_ACCESS_KEY,
                                  aws_secret_access_key=settings.S3_SECRET_KEY,
                                  region_name=settings.S3_REGION_NAME,
                                  endpoint_url=settings.S3_ENDPOINT_URL)

        progress_recorder.set_progress(
            0, 100, "2/2 Upload Original File to S3")

        # dest_directory should ends with /, we checked it in view when we created the task
        s3_task.upload_file(
            f"{temp_download_directory}{filename_with_extension}",
            remote_file_addr,
            "media-content",
            s3_storage,
            task_id,
            self,
            "2/2 Upload Original File to S3"
        )

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


@shared_task(bind=True)
def download_video_task(self, video_url: str,
                        meta_data: dict,
                        desire_format: str,
                        subtitles: list,
                        remote_dir: str,
                        user: str) -> "str":
    '''
    Download the video from m3u8 playlist (with subs if available)
    '''
    try:
        full_name = meta_data["full_name"]
        full_name_ext = f"{full_name}.{desire_format}"
        local_download_dir = f"{settings.TEMP_DOWNLOAD_DIR}{user}/{full_name.lower().replace(' ', '-')}"

        temp_download_directory_ops(
            full_name_ext, temp_download_directory=local_download_dir)
        progress_recorder = ProgressRecorder(self)
        progress_description = "1/3 Downloading video"
        progress_recorder.set_progress(0, 100, progress_description)

        task_id = self.request.id

        # Upload Files to S3 Storage
        s3_storage = boto3.client('s3', aws_access_key_id=settings.S3_ACCESS_KEY,
                                  aws_secret_access_key=settings.S3_SECRET_KEY,
                                  region_name=settings.S3_REGION_NAME,
                                  endpoint_url=settings.S3_ENDPOINT_URL)

        download(video_url, progress_recorder, progress_description,
                 split_by=20, file_name=full_name_ext, download_dir=local_download_dir)

        progress_description = "2/3 Downloading subtitles"
        progress_recorder.set_progress(0, 100, progress_description)
        download_subtitle(subtitles, full_name, progress_recorder,
                          progress_description, local_download_dir)

        progress_description = "3/3 Upload Video Directory to S3"
        progress_recorder.set_progress(0, 100, progress_description)
        # remote_folder should not ends with / becuase we add / after it here
        s3_task.upload_files(local_download_dir,
                             f"{remote_dir}/",
                             "media-content",
                             s3_storage,
                             progress_recorder,
                             progress_description)

    except Exception as error:
        print("\nError Occurred!! \n" + str(error))

    finally:
        for filename in os.listdir(local_download_dir):
            file_path = os.path.join(local_download_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as error:
                print(f'Failed to delete {file_path}. Reason: {error}')
        os.rmdir(local_download_dir)


@shared_task(bind=True)
def download_m3u8_video_task(self, m3u8_url: str,
                             stream: str,
                             meta_data: dict,
                             desire_format,
                             subtitles: list,
                             remote_dir: str,
                             user: str) -> "str":
    '''
    Download the video from m3u8 playlist (with subs if available)
    '''
    try:
        full_name = meta_data["full_name"]
        full_name_ext = f"{full_name}.{desire_format}"
        local_download_dir = f"{settings.TEMP_DOWNLOAD_DIR}{user}/{full_name.lower().replace(' ', '-')}"

        temp_download_directory_ops(
            full_name_ext, temp_download_directory=local_download_dir)
        progress_recorder = ProgressRecorder(self)

        task_id = self.request.id

        # Upload Files to S3 Storage
        s3_storage = boto3.client('s3', aws_access_key_id=settings.S3_ACCESS_KEY,
                                  aws_secret_access_key=settings.S3_SECRET_KEY,
                                  region_name=settings.S3_REGION_NAME,
                                  endpoint_url=settings.S3_ENDPOINT_URL)

        progress_description = "1/3 Downloading subtitles"
        progress_recorder.set_progress(0, 100, progress_description)
        download_subtitle(subtitles, full_name, progress_recorder,
                          progress_description, local_download_dir)

        progress_description = "2/3 Downloading video from M3U8 file"
        progress_recorder.set_progress(0, 100, progress_description)
        urls = parse_m3u8_media(m3u8_url, stream)
        m3u8_to_video(urls["v"], urls["a"], progress_recorder,
                      progress_description, meta_data, desire_format, download_dir=local_download_dir)


        progress_description = "3/3 Upload Video Directory to S3"
        progress_recorder.set_progress(0, 100, progress_description)
        # remote_folder should not ends with / becuase we add / after it here
        s3_task.upload_files(local_download_dir,
                             f"{remote_dir}/",
                             "media-content",
                             s3_storage,
                             progress_recorder,
                             progress_description)

    except Exception as error:
        print("\nError Occurred!! \n" + str(error))

    finally:
        for filename in os.listdir(local_download_dir):
            file_path = os.path.join(local_download_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as error:
                print(f'Failed to delete {file_path}. Reason: {error}')
        os.rmdir(local_download_dir)
