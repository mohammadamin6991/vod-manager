from rest_framework import serializers


# We now have a better separation, with separate required, allow_null and allow_blank arguments.

# The following set of arguments are used to control validation of empty values:

#     required=False: The value does not need to be present in the input, and will not be passed to .create() or .update() if it is not seen.
#     default=<value>: The value does not need to be present in the input, and a default value will be passed to .create() or .update() if it is not seen.
#     allow_null=True: None is a valid input.
#     allow_blank=True: '' is valid input. For CharField and subclasses only.

# Typically you'll want to use required=False if the corresponding model field has a default value, and additionally set either allow_null=True or allow_blank=True if required.

# The default argument is also available and always implies that the field is not required to be in the input. It is unnecessary to use the required argument when a default is specified, and doing so will result in an error.

# Ref: https://www.django-rest-framework.org/community/3.0-announcement/#the-required-allow_null-allow_blank-and-default-arguments


class DownloadFileSerializer(serializers.Serializer):
    file_url = serializers.URLField(required=True, allow_blank=False)
    dest_filename = serializers.CharField(
        required=False, allow_blank=False, allow_null=False, default=None)
    dest_directory = serializers.CharField(
        required=False, allow_blank=False, allow_null=False, trim_whitespace=True, default=None)


class DownloadM3U8Video(serializers.Serializer):
    m3u8_url = serializers.URLField(
        required=True, allow_blank=False, allow_null=False)
    video_name = serializers.CharField(
        required=True, allow_blank=False, allow_null=False)
    desire_format = serializers.CharField(
        required=True, allow_blank=False, allow_null=False)
    stream_media = serializers.CharField(
        required=True, allow_blank=False, allow_null=False)

    # Subs if any
    subtitles = serializers.ListField(
        required=False, allow_null=False, default=None)

    # Use for converting with ffmpeg
    codec = serializers.CharField(
        required=False, allow_null=False, default=None)

    # For naming and location
    year = serializers.CharField(
        required=False, allow_null=False, default="")
    quality = serializers.CharField(
        required=False, allow_null=False, default="")
    dest_dir = serializers.CharField(
        required=False, allow_null=False, default=None)


class DownloadVideo(serializers.Serializer):
    '''
    DownloadVideo request paramtere serializer
    '''
    video_url = serializers.URLField(
        required=True, allow_blank=False, allow_null=False)
    video_name = serializers.CharField(
        required=True, allow_blank=False, allow_null=False)
    desire_format = serializers.CharField(
        required=False, allow_blank=False, allow_null=False, default=None)

    # Subs if any
    subtitles = serializers.ListField(
        required=False, allow_null=False, default=None)

    # Use for converting with ffmpeg
    codec = serializers.CharField(
        required=False, allow_null=False, default=None)

    # For naming and location
    year = serializers.CharField(
        required=False, allow_null=False, default="")
    quality = serializers.CharField(
        required=False, allow_null=False, default="")
    dest_dir = serializers.CharField(
        required=False, allow_null=False, default=None)
