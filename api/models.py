from django.db import models
from djongo import models


# Create your models here.
class MediaFile(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='media/')
    watermark = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.title