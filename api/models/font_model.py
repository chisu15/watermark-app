import mongoengine as me
from datetime import datetime

class Font(me.Document):
    name = me.StringField(max_length=255, required=True)  # Tên font, ví dụ: "Roboto Bold"
    file_path = me.StringField(required=True)  # Đường dẫn đến tệp font đã lưu
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'fonts',
        'indexes': [
            'name',
            'created_at',
        ],
    }

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Automatically update the `updated_at` field when saving the document
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super(Font, self).save(*args, **kwargs)
