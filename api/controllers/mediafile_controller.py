from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import FileSystemStorage
import uuid
import os
from ..models.mediafile_model import MediaFile, Watermark
from ..utils.json_encoder import CustomJSONEncoder
from ..utils.json_utils import mongo_to_dict
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


class Index(APIView):
    def get(self, request):
        media_files = MediaFile.objects.all()
        media_files_list = []
        for media_file in media_files:
            media_file_data = mongo_to_dict(media_file.to_mongo().to_dict())
            media_file_data["file_path"] = request.build_absolute_uri(
                media_file.file_path
            )
            if media_file.file_watermarked:
                media_file_data["file_watermarked"] = request.build_absolute_uri(
                    media_file.file_watermarked
                )
            media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)


class Detail(APIView):
    def get(self, request, mediafile_id):
        media_file = MediaFile.objects(id=mediafile_id).first()
        if media_file:
            media_file_data = mongo_to_dict(media_file.to_mongo().to_dict())
            media_file_data["file_path"] = request.build_absolute_uri(
                media_file.file_path
            )
            if media_file.file_watermarked:
                media_file_data["file_watermarked"] = request.build_absolute_uri(
                    media_file.file_watermarked
                )
            return Response(media_file_data, status=status.HTTP_200_OK)
        return Response(
            {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
        )


class Create(APIView):
    def post(self, request):
        data = request.data
        file = request.FILES.get("file")
        if file:
            fs = FileSystemStorage()
            extension = os.path.splitext(file.name)[1]
            filename = str(uuid.uuid4()) + extension
            saved_filename = fs.save(filename, file)
            file_url = fs.url(saved_filename)

            file_size = file.size
            file_type = file.content_type
            file_name = file.name
            width, height = None, None

            # Extract image dimensions if the file is an image
            if file_type.startswith("image"):
                from PIL import Image

                image = Image.open(file)
                width, height = image.size

            media_file = MediaFile(
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                file_path=file_url,
                width=width,
                height=height,
                description=data.get("description", ""),
            )
            media_file.save()
            return Response(
                {"message": "Media file added", "id": str(media_file.id)},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )


class Edit(APIView):
    def patch(self, request, mediafile_id):
        media_file = MediaFile.objects(id=mediafile_id).first()
        if not media_file:
            return Response(
                {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        if "description" in data:
            media_file.description = data["description"]

        file = request.FILES.get("file")
        if file:
            old_file_path = media_file.file_path
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

            file_size = file.size
            file_type = file.content_type
            file_name = file.name
            width, height = None, None

            if file_type.startswith("image"):
                from PIL import Image

                image = Image.open(file)
                width, height = image.size

            media_file.file_name = file_name
            media_file.file_type = file_type
            media_file.file_size = file_size
            media_file.file_path = file_url
            media_file.width = width
            media_file.height = height

        media_file.save()
        return Response({"message": "Media file updated"}, status=status.HTTP_200_OK)


class Delete(APIView):
    def delete(self, request, mediafile_id):
        media_file = MediaFile.objects(id=mediafile_id).first()
        if not media_file:
            return Response(
                {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
            )

        file_path = media_file.file_path
        if file_path:
            absolute_file_path = os.path.normpath(
                os.path.join(settings.MEDIA_ROOT, file_path.lstrip("/"))
            )
            if os.path.isfile(absolute_file_path):
                os.remove(absolute_file_path)

        media_file.delete()
        return Response(
            {"message": "Media file deleted"}, status=status.HTTP_204_NO_CONTENT
        )


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


class ApplyWatermark(APIView):
    def post(self, request, mediafile_id):
        media_file = MediaFile.objects(id=mediafile_id).first()
        if not media_file:
            return Response(
                {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
            )
        print("SSDAdasd", os.path.join(settings.BASE_DIR, "fonts\ROBOTO-BOLD.ttf"))
        data = request.data
        # Kiểm tra xem các trường bắt buộc có trong yêu cầu không
        required_fields = [
            "type",
            "content",
            "position_x",
            "position_y",
            "opacity",
            "size",
            "color"
        ]
        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"Missing field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )


        hex_color = data["color"]
        rgb_color = hex_to_rgb(hex_color)
        watermark_options = Watermark(
            type=data["type"],
            content=data["content"],
            position_x=float(data["position_x"]),
            position_y=float(data["position_y"]),
            opacity=float(data["opacity"]),
            size=float(data["size"]),
            color=hex_color,
        )

        # Apply watermark to the image
        file_path = media_file.file_path
        file_path = file_path[len("/media") :]
        file_path = file_path.lstrip("/")
        absolute_file_path = os.path.normpath(
            os.path.join(settings.MEDIA_ROOT, file_path)
        )

        if not os.path.exists(absolute_file_path):
            return Response(
                {"error": "File not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            image = Image.open(absolute_file_path).convert("RGBA")
            txt = Image.new("RGBA", image.size, (255, 255, 255, 0))

            draw = ImageDraw.Draw(txt)
            font_size = int(watermark_options.size)
            font_path = os.path.join(settings.BASE_DIR, "fonts", "Roboto-Bold.ttf")
            if not os.path.exists(font_path):
                return Response({"error": "Font not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            font = ImageFont.truetype(font_path, font_size)


            text = watermark_options.content
            position = (watermark_options.position_x, watermark_options.position_y)

            draw.text(
                position,
                text,
                font=font,
                fill=(
                    rgb_color[0],
                    rgb_color[1],
                    rgb_color[2],
                    int(watermark_options.opacity * 255),
                ),
            )

            watermarked = Image.alpha_composite(image, txt)
            watermarked = watermarked.convert("RGB")

            # SAVE FILE
            fs = FileSystemStorage()
            extension = os.path.splitext(file_path)[1]
            filename = str(uuid.uuid4()) + "_watermarked" + extension

            # Save image to BytesIO
            img_io = BytesIO()
            watermarked.save(img_io, format=watermarked.format or "PNG")
            img_io.seek(0)  # Đặt lại con trỏ về đầu stream

            saved_filename = fs.save(filename, img_io)
            watermarked_url = fs.url(saved_filename)

            media_file.watermark_options = watermark_options
            media_file.file_watermarked = watermarked_url
            media_file.save()

            return Response(
                {
                    "code" : 200,
                    "message": "Watermark applied successfully",
                    "file_path": watermarked_url,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "code": 500,
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
