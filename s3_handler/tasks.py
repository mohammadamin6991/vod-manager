''' import modules '''
import os
import threading
from celery import shared_task


class ProgressPercentage(object):

    def __init__(self, filename, task_id, task, description):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self.task_id = task_id
        self.task = task
        self.description = description

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100

        # if int(datetime.datetime.now().timestamp() * 10) % 2 == 0:

        meta={
            "pending": False,
            "current": self._seen_so_far,
            "total": self._size,
            "percent": percentage,
            "description": self.description
        }
        self.task.update_state(task_id=self.task_id, state='TRANSCODING', meta=meta)


@shared_task
def upload_file(local_address, remote_address, bucket_name, s3_handler, task_id, task, description):
    ''' upload a file to s3 '''
    callback = ProgressPercentage(local_address, task_id, task, description)
    s3_handler.upload_file(local_address, bucket_name, remote_address, Callback=callback)

@shared_task
def upload_files(local_directory, remote_folder, bucket_name, s3_handler, progress_recorder, description):
    ''' upload a directory to s3 '''

    maxval = len([name for name in os.listdir(local_directory) if os.path.isfile(os.path.join(local_directory, name))])
    current = 0
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            s3_handler.upload_file(local_path, bucket_name, f"{remote_folder}{file}")
            progress_recorder.set_progress(current, maxval, description)
            current = current + 1
