import os
import time
import math
import urllib.request as urllib2
import requests
import m3u8
import ffmpeg
from django.conf import settings
from django.http import HttpRequest
from celery_progress.backend import ProgressRecorder


def check_username_token_extraction(request: HttpRequest) -> None:
    ''' Raise exception if it can not extract username from JWT token '''
    if not request.user.username:
        raise Exception("Can not extract username from token!")

def build_range(value, numsplits):
    '''
    create download bytes range according to number of parts
    '''
    chunk_size = math.ceil(value / numsplits)
    lst = []
    for i in range(numsplits):
        if i == 0:
            lst.append(f"{i}-{chunk_size}")
        elif i == numsplits - 1:
            lst.append(f"{i * chunk_size + 1}-{value}")
        else:
            lst.append(f"{i * chunk_size + 1}-{(i + 1) * chunk_size}")
    return lst

def download_chunk(url, idx, irange):
    range_header = f'bytes={irange}'
    req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    req.headers['Range'] = range_header
    return urllib2.urlopen(req).read()

def download_single_part(url: str):
    req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib2.urlopen(req).read()

def temp_download_directory_ops(file_name: str,
                                clean_all=False,
                                temp_download_directory=settings.TEMP_DOWNLOAD_DIR):
    '''
    Create templ download directory if no exists.
    Delete old file with a same name if exists.
    '''

    if not temp_download_directory.endswith("/"):
        temp_download_directory = temp_download_directory + "/"

    file_path = f"{temp_download_directory}{file_name}"
    if not os.path.exists(temp_download_directory):
        os.makedirs(temp_download_directory)
        print("khob sakhtamesh!")
    if os.path.exists(file_path):
        os.remove(file_path)
        print("file e bood, pakesh kardam")


def download_subtitle(subtitles: list,
                      video_name: str,
                      progress_recorder: ProgressRecorder,
                      progress_description: str,
                      video_local_dir: str):
    ''' Download subtitles for a specefic video '''

    for subtitle in subtitles:
        subtitle_url = '#'.join(subtitle.split("#")[0:-2])
        subtitle_lang = subtitle.split('#')[-2]
        subtitle_format = subtitle.split('#')[-1]

        subtitle_parsed_name = f"{video_name}.{subtitle_lang}.{subtitle_format}"
        # Download URL and store it locally
        download(subtitle_url, progress_recorder, progress_description, split_by=1,
                 file_name=subtitle_parsed_name, download_dir=video_local_dir)


def download(url: str,
             progress_recorder: ProgressRecorder,
             progress_description: str,
             split_by: int = 8,
             file_name: str = None,
             download_dir: str =settings.TEMP_DOWNLOAD_DIR) -> "str":
    '''
    split a url file and download it.

    '''
    start_time = time.time()
    if not url:
        print("Please Enter some url to begin download.")
        raise Exception("Invalid URL")

    if file_name is None:
        file_name = url.split('/')[-1]

    temp_download_directory_ops(
        file_name, temp_download_directory=download_dir)

    # filename_with_extension = downloaded_file_full_path.split('/')[-1]
    # filename_without_extension = os.path.splitext(filename_with_extension)[0]

    headers = {
        'Accept-Encoding': 'identity',
        'User-Agent': 'Mozilla/5.0'
    }
    size_in_bytes = requests.head(
        url, headers=headers, timeout=1000).headers.get('content-length', None)
    print(f"{size_in_bytes} bytes to download.")

    defined_size = True
    if not size_in_bytes:
        print("Size cannot be determined.")
        defined_size = False

    if not download_dir.endswith("/"):
        download_dir = download_dir + "/"
    file_path = download_dir + file_name

    if defined_size:
        # split total num bytes into ranges
        ranges = build_range(int(size_in_bytes), split_by)

        # reassemble file in correct order
        with open(file_path, 'wb') as downloaded_file:
            for idx, irange in enumerate(ranges):
                print(progress_recorder)
                chunk = download_chunk(url, idx, irange)
                downloaded_file.write(chunk)
                progress_recorder.set_progress(
                    (idx + 1), len(ranges), progress_description)

    else:
        with open(file_path, 'wb') as downloaded_file:
            chunk = download_single_part(url)
            downloaded_file.write(chunk)
            progress_recorder.set_progress(
                1, 1, progress_description)

    print(f"--- { str(time.time() - start_time) } seconds ---")

    print(f"Finished Writing file {file_name}")
    print(f"file size {os.path.getsize(file_path)} bytes")

    return file_path


# ffmpeg -i "http://host/folder/file.m3u8" -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 file.mp4
# ffmpeg.input(new_filename).output(h264_stream, vcodec='copy', **{'bsf:v': h264_mp4toannexb'}).compile()
def m3u8_to_video(video_url: str,
                  audio_url: str,
                  progress_recorder: ProgressRecorder,
                  progress_description: str,
                  meta_data: dict,
                  desire_format: str,
                  download_dir=settings.TEMP_DOWNLOAD_DIR):
    '''
    Using ffmpeg to download m3u8 segments and assemble it into a single video file
    '''
    if not download_dir.endswith("/"):
        download_dir = download_dir + "/"

    video_local_addr = f"{download_dir}{meta_data['full_name']}.{desire_format}"

    stream = (
        ffmpeg
        .input(video_url)
        .output(video_local_addr, acodec='copy', vcodec='copy')
    )
    if audio_url is not None:
        print(f"audio_url is not None: {audio_url}")
        stream.global_args('-i', audio_url).run()
    else:
        stream.run()


# https://github.com/globocom/m3u8
# https://www.rfc-editor.org/rfc/rfc8216#section-4.3.4.1
def parse_m3u8_media(master_url: str,
                     v_quality: str = "1080",
                     a_channel: int = 2) -> "dict":
    '''
    Parse m3u8 playlist and extract audio and video stream urls base on the input args
    '''
    base_url = os.path.dirname(master_url)
    playlist_obj = m3u8.load(master_url)
    video_uri = None
    audio_uri = None
    for playlist in playlist_obj.playlists:
        # Check if we want this media
        res = (playlist.stream_info.resolution)[-1]
        if int(res) == int(v_quality):
            print(playlist.uri)
            video_uri = playlist.uri
            # Check if it has additional media (eg audio)
            if len(playlist.media) > 0:
                for media in playlist.media:
                    # Select proper audio channel
                    if int(media.channels) == int(a_channel):
                        audio_uri = media.uri

    if video_uri is None and audio_uri is None:
        raise Exception("No Media found")

    if video_uri is not None:
        video_url = f"{base_url}/{video_uri}"
    else:
        video_url = None

    if audio_uri is not None:
        audio_url = f"{base_url}/{audio_uri}"
    else:
        audio_url = None

    return {"v": video_url, "a": audio_url}
