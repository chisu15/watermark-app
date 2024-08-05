import os
import uuid
import json
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..models.mediafile_model import MediaFile
from ..utils.json_encoder import CustomJSONEncoder
from django.core.files.storage import default_storage
from django.conf import settings

class Index(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mediafile = MediaFile()
    def get(self, request, mediafile_id=None):
        if mediafile_id:
            media_file = self.mediafile.get(mediafile_id)
            if media_file:
                return Response(
                    json.loads(json.dumps(media_file, cls=CustomJSONEncoder)),
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
            )
        media_files = self.mediafile.list_all()
        return Response(
            json.loads(json.dumps(media_files, cls=CustomJSONEncoder)),
            status=status.HTTP_200_OK,
        )


class Create(APIView):
    def post(self, request):
        data = request.data
        file = request.FILES.get("file")
        
        if file:
            fs = FileSystemStorage()
            # Lấy phần mở rộng của file
            extension = os.path.splitext(file.name)[1]
            # Tạo tên file mới với uuid
            filename = str(uuid.uuid4()) + extension
            # Lưu file với tên mới
            saved_filename = fs.save(filename, file)
            file_url = fs.url(saved_filename)
            
            data["file_path"] = file_url
            media_id = MediaFile().create(
                data.get("title"), data.get("file_path"), data.get("description")
            )
            return Response(
                {"code": 201,"message": "Media file added", "id": media_id},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )


class Detail(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mediafile = MediaFile()

    def get(self, request, mediafile_id):
        print(mediafile_id)
        media_file = self.mediafile.get(mediafile_id)
        if media_file:
            return Response(
                json.loads(json.dumps(media_file, cls=CustomJSONEncoder)),
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
        )


class Edit(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mediafile = MediaFile()

    def patch(self, request, mediafile_id):
        data = {}
        title = request.data.get("title")
        description = request.data.get("description")
        
        if title:
            data["title"] = title
        if description:
            data["description"] = description

        file = request.FILES.get("file")
        if file:
            # Lấy thông tin file cũ từ cơ sở dữ liệu
            old_file_path = self.mediafile.get(mediafile_id).get("file_path")
            if old_file_path:
                # Chuyển đổi đường dẫn file cũ thành đường dẫn tuyệt đối
                absolute_old_file_path = os.path.join(settings.BASE_DIR, old_file_path.lstrip("/"))
                if os.path.exists(absolute_old_file_path):
                    try:
                        os.remove(absolute_old_file_path)
                        print(f"File {absolute_old_file_path} deleted successfully.")
                    except Exception as e:
                        print(f"Error deleting file {absolute_old_file_path}: {str(e)}")
                        return Response({"error": f"Error deleting old file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    print(f"File {absolute_old_file_path} not found.")
            
            # Lưu file mới
            fs = FileSystemStorage()
            extension = os.path.splitext(file.name)[1]
            filename = str(uuid.uuid4()) + extension
            saved_filename = fs.save(filename, file)
            file_url = fs.url(saved_filename)
            data["file_path"] = file_url

        update_count = self.mediafile.update(mediafile_id, data)
        if update_count:
            return Response(
                {"code": 200, "message": "Media file updated"}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND
        )
        
        
class Delete(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mediafile = MediaFile()

    def delete(self, request, mediafile_id):
        media_file = self.mediafile.get(mediafile_id)
        if not media_file:
            return Response({"error": "Media file not found"}, status=status.HTTP_404_NOT_FOUND)

        file_path = media_file.get('file_path')
        print("Original file_path from DB: ", file_path)
        
        if file_path:
            # Xóa tiền tố "/media" nếu tồn tại
            if file_path.startswith("/media"):
                file_path = file_path[len("/media"):]
            print("file_path after removing /media: ", file_path)

            # Chuẩn hóa đường dẫn
            file_path = file_path.lstrip("/")
            absolute_file_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_path))
            print("absolute_file_path: ", absolute_file_path)
            
            # Kiểm tra và xóa file nếu tồn tại
            if os.path.isfile(absolute_file_path):
                try:
                    os.remove(absolute_file_path)
                    print(f"File {absolute_file_path} deleted successfully.")
                except Exception as e:
                    print(f"Error deleting file {absolute_file_path}: {str(e)}")
                    return Response({"error": f"Error deleting file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                print(f"File {absolute_file_path} not found.")
                
        delete_count = self.mediafile.delete(mediafile_id)
        if delete_count:
            return Response({"message": "Media file and associated file deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Error deleting media file from database"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)