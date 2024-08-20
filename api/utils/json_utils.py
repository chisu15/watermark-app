# utils/json_utils.py
import mongoengine as me
from bson import ObjectId
from datetime import datetime, date

def mongo_to_dict(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, me.EmbeddedDocument):
        return {field: mongo_to_dict(getattr(obj, field)) for field in obj._fields}
    elif isinstance(obj, list):
        return [mongo_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: mongo_to_dict(value) for key, value in obj.items()}
    else:
        return obj
