import mongoengine as me
from datetime import datetime

class Watermark(me.EmbeddedDocument):
    type = me.StringField(required=True)
    content = me.StringField(required=True)
    position_x = me.FloatField(required=True)
    position_y = me.FloatField(required=True)
    opacity = me.FloatField(required=True)
    size = me.FloatField(required=True)
    color = me.StringField(required=True) 
    font_id = me.StringField(required=True)

class MediaFile(me.Document):
    file_name = me.StringField(max_length=255, required=True)
    file_type = me.StringField(max_length=50, required=True)
    file_size = me.IntField(required=True)
    file_path = me.StringField(required=True)
    width = me.IntField(required=False)
    height = me.IntField(required=False)
    description = me.StringField()
    watermark_options = me.EmbeddedDocumentField(Watermark, required=False)
    file_watermarked = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.StringField(max_length=255, required=False)

    meta = {
        'collection': 'media_files',
        'indexes': [
            'file_name',
            'file_type',
            'created_at',
        ],
    }

    def __str__(self):
        return self.file_name
