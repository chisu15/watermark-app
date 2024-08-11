from rest_framework import serializers
from .models import MediaFile

class WatermarkSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    content = serializers.CharField(max_length=255)
    position_x = serializers.FloatField()
    position_y = serializers.FloatField()
    opacity = serializers.FloatField()
    size = serializers.FloatField()
    color = serializers.CharField(max_length=7)  # Assuming hex color like #FFFFFF

class MediaFileSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255)
    file_type = serializers.CharField(max_length=50)
    file_size = serializers.IntegerField()
    file_path = serializers.CharField(max_length=1024)
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    watermark_options = WatermarkSerializer(required=False, allow_null=True)
    file_watermarked = serializers.CharField(max_length=1024, required=False, allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def create(self, validated_data):
        watermark_data = validated_data.pop('watermark_options', None)
        if watermark_data:
            watermark = WatermarkSerializer(data=watermark_data)
            if watermark.is_valid():
                validated_data['watermark_options'] = watermark.save()
        return MediaFile(**validated_data)

    def update(self, instance, validated_data):
        instance.file_name = validated_data.get('file_name', instance.file_name)
        instance.file_type = validated_data.get('file_type', instance.file_type)
        instance.file_size = validated_data.get('file_size', instance.file_size)
        instance.file_path = validated_data.get('file_path', instance.file_path)
        instance.width = validated_data.get('width', instance.width)
        instance.height = validated_data.get('height', instance.height)
        instance.description = validated_data.get('description', instance.description)

        watermark_data = validated_data.get('watermark_options', None)
        if watermark_data:
            watermark = WatermarkSerializer(instance=instance.watermark_options, data=watermark_data)
            if watermark.is_valid():
                instance.watermark_options = watermark.save()

        instance.file_watermarked = validated_data.get('file_watermarked', instance.file_watermarked)
        instance.updated_at = validated_data.get('updated_at', instance.updated_at)

        instance.save()
        return instance
