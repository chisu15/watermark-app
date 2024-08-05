from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .configs.mongodb import MongoDB

class MediaFileView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = MongoDB()
        self.collection = self.db.get_collection('mediafiles')

    def get(self, request):
        media_files = list(self.collection.find({}))
        return Response(media_files, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        self.collection.insert_one(data)
        return Response({"message": "Media file added"}, status=status.HTTP_201_CREATED)
