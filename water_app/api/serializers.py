# api/serializers.py
from rest_framework import serializers

class MediaFileSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200)
    file_path = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=500, required=False)
