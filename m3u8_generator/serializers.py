from rest_framework import serializers

class M3U8Serializer(serializers.Serializer):
    video_url = serializers.URLField(min_length=None, required=True, allow_blank=False)
    maxq = serializers.IntegerField(min_value=360, max_value=2160, required=False, default=None)

