from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import FileSystemStorage
import uuid
import os
from ..models.font_model import Font
from ..utils.json_utils import mongo_to_dict
from django.conf import settings
from PIL import ImageFont


class FontIndex(APIView):
    def get(self, request):
        fonts = Font.objects.all()
        fonts_list = []
        for font in fonts:
            font_data = mongo_to_dict(font.to_mongo().to_dict())
            font_data["file_path"] = request.build_absolute_uri(font.file_path)
            fonts_list.append(font_data)
        return Response(fonts_list, status=status.HTTP_200_OK)


class FontDetail(APIView):
    def get(self, request, font_id):
        font = Font.objects(id=font_id).first()
        if font:
            font_data = mongo_to_dict(font.to_mongo().to_dict())
            font_data["file_path"] = request.build_absolute_uri(font.file_path)
            return Response(font_data, status=status.HTTP_200_OK)
        return Response(
            {"error": "Font not found"}, status=status.HTTP_404_NOT_FOUND
        )


class FontCreate(APIView):
    def post(self, request):
        data = request.data
        file = request.FILES.get("file")
        if file:
            fs = FileSystemStorage()
            extension = os.path.splitext(file.name)[1]
            filename = str(uuid.uuid4()) + extension
            saved_filename = fs.save(filename, file)
            file_url = fs.url(saved_filename)

            font_name = data.get("name", file.name)
            font_size = data.get("size", None)

            font = Font(
                name=font_name,
                file_path=file_url,
                file_size=file.size,
                file_type=file.content_type,
                font_size=font_size,
            )
            font.save()
            return Response(
                {"message": "Font added", "id": str(font.id)},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )


class FontEdit(APIView):
    def patch(self, request, font_id):
        font = Font.objects(id=font_id).first()
        if not font:
            return Response(
                {"error": "Font not found"}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        if "name" in data:
            font.name = data["name"]
        if "size" in data:
            font.font_size = data["size"]

        file = request.FILES.get("file")
        if file:
            old_file_path = font.file_path
            if old_file_path:
                absolute_old_file_path = os.path.join(
                    settings.MEDIA_ROOT, old_file_path.lstrip("/")
                )
                if os.path.exists(absolute_old_file_path):
                    os.remove(absolute_old_file_path)

            fs = FileSystemStorage()
            extension = os.path.splitext(file.name)[1]
            filename = str(uuid.uuid4()) + extension
            saved_filename = fs.save(filename, file)
            file_url = fs.url(saved_filename)

            font.file_path = file_url
            font.file_size = file.size
            font.file_type = file.content_type

        font.save()
        return Response({"message": "Font updated"}, status=status.HTTP_200_OK)


class FontDelete(APIView):
    def delete(self, request, font_id):
        font = Font.objects(id=font_id).first()
        if not font:
            return Response(
                {"error": "Font not found"}, status=status.HTTP_404_NOT_FOUND
            )

        file_path = font.file_path
        if file_path:
            absolute_file_path = os.path.normpath(
                os.path.join(settings.MEDIA_ROOT, file_path.lstrip("/"))
            )
            if os.path.isfile(absolute_file_path):
                os.remove(absolute_file_path)

        font.delete()
        return Response(
            {"message": "Font deleted"}, status=status.HTTP_204_NO_CONTENT
        )
