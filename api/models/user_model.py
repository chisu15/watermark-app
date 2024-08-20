
import mongoengine as me
from datetime import datetime
from django.db import models

class User(me.Document):
    email = me.StringField(required=True, unique=True)
    username = me.StringField(max_length=255, required=True)
    profile_picture = me.StringField(null=True, blank=True)
    google_id = me.StringField(max_length=255, unique=True, null=True, blank=True)
    last_login_time = me.DateTimeField(default=datetime.utcnow)
    objects = models.Manager() 

    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'google_id',
        ],
    }

    def __str__(self):
        return self.email