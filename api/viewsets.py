from rest_framework import viewsets
from .models import MediaFile
from .serializers import MediaFileSerializer

class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
