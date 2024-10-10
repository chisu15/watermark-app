from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import FileSystemStorage
import uuid
import os
from ..models.mediafile_model import MediaFile, Watermark
from ..models.user_model import User
from ..utils.json_utils import mongo_to_dict
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from google.oauth2 import id_token
from google.auth.transport import requests
import moviepy.editor as mp
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from moviepy.editor import VideoFileClip

class Index(APIView):
    def get(self, request):

        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
        print("token: ", token)

        # Verify token với Google
        idInfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        user = User.objects.get(google_id=idInfo["sub"])
        print("idInfo: ", idInfo)
        print("idInfo: ", str(user.id))
        dataUser = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "last_login_time": user.last_login_time,
        }
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
            if media_file.created_by == dataUser["id"]:
                media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)


class Detail(APIView):
    def get(self, request, mediafile_id):
        # Lấy token từ cookie
        # token = request.COOKIES.get("token")
        # if not token:
        #     return Response(
        #         {"detail": "Token not provided"}, status=status.HTTP_401_UNAUTHORIZED
        #     )
        media_file = MediaFile.objects(id=mediafile_id).first()
        font_path = media_file.file_path
        font_path = font_path[len("/media") :]
        font_path = font_path.lstrip("/")
        absolute_font_path = os.path.normpath(
            os.path.join(settings.MEDIA_ROOT, font_path)
        )
        print(absolute_font_path)
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


class GetListFont(APIView):
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
            if media_file.file_type.startswith("font"):
                media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)


class GetListImage(APIView):
    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
        print("token: ", token)

        # Verify token với Google
        idInfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        user = User.objects.get(google_id=idInfo["sub"])
        print("idInfo: ", idInfo)
        print("idInfo: ", str(user.id))
        dataUser = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "last_login_time": user.last_login_time,
        }
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
            if (
                media_file.file_type.startswith("image")
                and media_file.created_by == dataUser["id"]
            ):
                media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)

class GetListVideo(APIView):
    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
        print("token: ", token)

        # Verify token với Google
        idInfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        user = User.objects.get(google_id=idInfo["sub"])
        print("idInfo: ", idInfo)
        print("idInfo: ", str(user.id))
        dataUser = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "last_login_time": user.last_login_time,
        }
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
            if (
                media_file.file_type.startswith("video")
                and media_file.created_by == dataUser["id"]
            ):
                media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)

class GetListVideo(APIView):
    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
        print("token: ", token)

        # Verify token với Google
        idInfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        user = User.objects.get(google_id=idInfo["sub"])
        print("idInfo: ", idInfo)
        print("idInfo: ", str(user.id))
        dataUser = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "last_login_time": user.last_login_time,
        }
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
            if (
                media_file.file_type.startswith("video")
                and media_file.created_by == dataUser["id"]
            ):
                media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)

class GetListPDF(APIView):
    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
        print("token: ", token)

        # Verify token với Google
        idInfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        user = User.objects.get(google_id=idInfo["sub"])
        print("idInfo: ", idInfo)
        print("idInfo: ", str(user.id))
        dataUser = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "last_login_time": user.last_login_time,
        }
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
            if (
                media_file.file_type.startswith("application")
                and media_file.created_by == dataUser["id"]
            ):
                media_files_list.append(media_file_data)

        return Response(media_files_list, status=status.HTTP_200_OK)



class Create(APIView):
    def post(self, request):

        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = parts[1]
        print("token: ", token)

        # Verify token với Google
        idInfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )

        user = User.objects.get(google_id=idInfo["sub"])
        print("idInfo: ", idInfo)
        print("idInfo: ", str(user.id))
        dataUser = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "last_login_time": user.last_login_time,
        }
        
        data = request.data
        file = request.FILES.get("file")
        if file:
            fs = FileSystemStorage()
            title = os.path.splitext(file.name)[0]
            extension = os.path.splitext(file.name)[1]
            filename = str(uuid.uuid4()) + extension
            saved_filename = fs.save(filename, file)
            file_url = fs.url(saved_filename)

            file_size = file.size
            file_type = file.content_type
            file_name = file.name
            width, height = None, None

            if file_type.startswith("image"):
                image = Image.open(file)
                width, height = image.size

            elif file_type.startswith("video"):
                try:
                    saved_file_path = fs.path(saved_filename)
                    video = VideoFileClip(saved_file_path)
                    width, height = video.size
                except Exception as e:
                    return Response({"error": f"Failed to read video dimensions: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            media_file = MediaFile(
                title = title,
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                file_path=file_url,
                width=width,
                height=height,
                description=data.get("description", ""),
                created_by=dataUser["id"],
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
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
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
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            print("Authorization header is missing")
        else:
            print(f"Authorization header received: {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Tách và kiểm tra token
        parts = auth_header.split(" ")
        if len(parts) != 2:
            return Response(
                {"detail": "Token not provided or invalid format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

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

        data = request.data
        hex_color = data["color"]
        rgb_color = hex_to_rgb(hex_color)

        # Lấy thông tin watermark từ request
        watermark_options = Watermark(
            type=data["type"],
            content=data["content"],
            position_x=float(data["position_x"]),
            position_y=float(data["position_y"]),
            opacity=float(data["opacity"]),
            size=float(data["size"]),
            color=hex_color,
            font_id=data["font"],
        )

        # Đường dẫn file
        file_extension = os.path.splitext(media_file.file_path)[1].lower()
        file_path = media_file.file_path
        file_path = file_path[len("/media"):]
        file_path = file_path.lstrip("/")
        absolute_file_path = os.path.normpath(
            os.path.join(settings.MEDIA_ROOT, file_path)
        )

        # Lấy font từ database
        font = MediaFile.objects(id=watermark_options.font_id).first()
        if not font:
            return Response(
                {"error": "Font not found"}, status=status.HTTP_404_NOT_FOUND
            )

        font_path = font.file_path
        font_path = font_path[len("/media"):]
        font_path = font_path.lstrip("/")
        absolute_font_path = os.path.normpath(
            os.path.join(settings.MEDIA_ROOT, font_path)
        )

        if not os.path.exists(absolute_font_path):
            return Response(
                {"error": "Font file not found"}, status=status.HTTP_404_NOT_FOUND
            )

        fontUsed = ImageFont.truetype(absolute_font_path, int(watermark_options.size))

        if file_extension in [".jpg", ".jpeg", ".png"]:
            # Xử lý watermark cho hình ảnh
            try:
                image = Image.open(absolute_file_path).convert("RGBA")
                txt = Image.new("RGBA", image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(txt)

                draw.text(
                    (watermark_options.position_x, watermark_options.position_y),
                    watermark_options.content,
                    font=fontUsed,
                    fill=(rgb_color[0], rgb_color[1], rgb_color[2], int(watermark_options.opacity * 255))
                )

                watermarked = Image.alpha_composite(image, txt).convert("RGB")

                # SAVE FILE
                fs = FileSystemStorage()
                filename = str(uuid.uuid4()) + "_watermarked" + file_extension
                img_io = BytesIO()
                watermarked.save(img_io, format="PNG")
                img_io.seek(0)

                saved_filename = fs.save(filename, img_io)
                watermarked_url = fs.url(saved_filename)

                media_file.file_watermarked = watermarked_url
                media_file.save()

                return Response(
                    {"code": 200, "message": "Watermark applied successfully", "file_path": watermarked_url},
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"code": 500, "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        elif file_extension == ".pdf":
            try:
                # Register custom font
                pdfmetrics.registerFont(TTFont('CustomFont', absolute_font_path))

                # Tạo watermark với font custom
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFont('CustomFont', watermark_options.size)
                can.setFillColorRGB(rgb_color[0]/255, rgb_color[1]/255, rgb_color[2]/255, watermark_options.opacity)
                can.drawString(watermark_options.position_x, watermark_options.position_y, watermark_options.content)
                can.save()

                packet.seek(0)
                watermark_pdf = PdfReader(packet)

                original_pdf = PdfReader(open(absolute_file_path, "rb"))
                output_pdf = PdfWriter()

                watermark_page = watermark_pdf.pages[0]

                for page_number in range(len(original_pdf.pages)):
                    original_page = original_pdf.pages[page_number]
                    original_page.merge_page(watermark_page)
                    output_pdf.add_page(original_page)

                pdf_io = BytesIO()
                output_pdf.write(pdf_io)
                pdf_io.seek(0)  # Đặt lại con trỏ về đầu stream

                # Lưu PDF watermarked vào FileSystemStorage
                fs = FileSystemStorage()
                filename = str(uuid.uuid4()) + "_watermarked.pdf"
                saved_filename = fs.save(filename, pdf_io)
                watermarked_url = fs.url(saved_filename)

                # Cập nhật file watermarked trong database
                media_file.file_watermarked = watermarked_url
                media_file.save()

                return Response(
                    {"code": 200, "message": "Watermark applied successfully", "file_path": media_file.file_watermarked},
                    status=status.HTTP_200_OK,
                )

            except Exception as e:
                return Response(
                    {"code": 500, "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        elif file_extension in [".mp4", ".mov", ".avi"]:
            try:
                # Load video
                video = mp.VideoFileClip(absolute_file_path)

                watermark = None

                if data["type"] == "text":
                    # Chuyển đổi hex màu sang RGB
                    hex_color = data["color"]
                    rgb_color = hex_to_rgb(hex_color)

                    # Lấy font từ database
                    font = MediaFile.objects(id=data["font"]).first()
                    if not font:
                        return Response(
                            {"error": "Font not found"}, status=status.HTTP_404_NOT_FOUND
                        )

                    font_path = font.file_path
                    font_path = font_path[len("/media"):]
                    font_path = font_path.lstrip("/")
                    absolute_font_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, font_path))

                    # Chuyển văn bản thành hình ảnh sử dụng Pillow
                    text_image_path = text_to_image(
                        data["content"],
                        absolute_font_path,
                        int(data["size"]),
                        (rgb_color[0], rgb_color[1], rgb_color[2], int(float(data["opacity"]) * 255)),
                    )

                    # Load the text image as a watermark
                    watermark = mp.ImageClip(text_image_path).set_duration(video.duration)

                elif data["type"] == "image":
                    # Xử lý file watermark_image được upload qua request
                    watermark_image_file = request.FILES.get('watermark_image')
                    if not watermark_image_file:
                        return Response(
                            {"error": "No watermark image provided"}, status=status.HTTP_400_BAD_REQUEST
                        )

                    # Lưu file watermark tạm thời
                    fs = FileSystemStorage()
                    watermark_image_filename = fs.save(f"{uuid.uuid4()}_watermark.png", watermark_image_file)
                    watermark_image_path = fs.path(watermark_image_filename)

                    # Load the PNG image for the watermark
                    watermark = mp.ImageClip(watermark_image_path).set_duration(video.duration)

                if watermark is None:
                    return Response(
                        {"error": "Watermark type not supported"}, status=status.HTTP_400_BAD_REQUEST
                    )

                # Đặt vị trí watermark
                watermark = watermark.set_position(
                    (float(data["position_x"]), float(data["position_y"]))
                ).set_opacity(float(data["opacity"]))

                # Composite video with watermark
                watermarked_video = mp.CompositeVideoClip([video, watermark])

                # Sử dụng FileSystemStorage để lưu video watermarked
                fs = FileSystemStorage()
                filename = str(uuid.uuid4()) + "_watermarked.mp4"
                saved_filepath = fs.path(filename)

                # Ghi file video watermarked
                # Ghi file video watermarked với alpha channel cho MOV
                if file_extension == ".mov":
                    watermarked_video.write_videofile(saved_filepath, codec="png", fps=24, withmask=True)
                else:
                    watermarked_video.write_videofile(saved_filepath, codec="libx264")
                # Lấy URL của file đã lưu
                watermarked_url = fs.url(filename)
                media_file.watermark_options = watermark_options
                media_file.file_watermarked = watermarked_url
                media_file.save()

                # Xóa file hình ảnh tạm nếu có
                if data["type"] == "text":
                    os.remove(text_image_path)
                elif data["type"] == "image":
                    os.remove(watermark_image_path)

                return Response(
                    {
                        "code": 200,
                        "message": "Watermark applied successfully",
                        "file_path": watermarked_url,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {"code": 500, "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response({"error": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Watermark applied successfully", "file_path": media_file.file_watermarked},
            status=status.HTTP_200_OK,
        )

def text_to_image(text, font_path, font_size, text_color, image_size=(500, 100)):
    # Tạo một hình ảnh mới với nền trong suốt
    img = Image.new('RGBA', image_size, (255, 255, 255, 0))  
    draw = ImageDraw.Draw(img)

    # Load font
    font = ImageFont.truetype(font_path, font_size)

    # Lấy bounding box của văn bản
    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]  # Chiều rộng của văn bản
    text_height = bbox[3] - bbox[1]  # Chiều cao của văn bản

    # Tính toán vị trí để căn giữa văn bản
    position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 2)

    # Vẽ văn bản lên hình ảnh
    draw.text(position, text, fill=text_color, font=font)

    # Tạo tệp tạm thời để lưu hình ảnh watermark
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        img.save(tmp_file.name, "PNG")
        temp_image_path = tmp_file.name

    return temp_image_path