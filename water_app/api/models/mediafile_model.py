from bson import ObjectId
from ..configs.mongodb import MongoDB

class MediaFile:
    def __init__(self):
        self.db = MongoDB().get_collection('mediafiles')

    def to_dict(self, mediafile):
        """Convert mediafile MongoDB document to dictionary."""
        return {
            "id": str(mediafile['_id']),  # Chuyển ObjectId thành chuỗi
            "title": mediafile.get('title', ''),
            "file_path": mediafile.get('file_path', ''),
            "description": mediafile.get('description', '')
        }

    def create(self, title, file_path, description=None):
        """Create a new media file document."""
        document = {
            'title': title,
            'file_path': file_path,
            'description': description
        }
        result = self.db.insert_one(document)
        return str(result.inserted_id)

    def get(self, mediafile_id):
        """Retrieve a media file by its ID."""
        mediafile = self.db.find_one({"_id": ObjectId(mediafile_id)})
        if mediafile:
            return self.to_dict(mediafile)
        return None

    def update(self, mediafile_id, update_data):
        """Update a media file document by its ID."""
        result = self.db.update_one({"_id": ObjectId(mediafile_id)}, {"$set": update_data})
        return result.modified_count

    def delete(self, mediafile_id):
        """Delete a media file document by its ID."""
        result = self.db.delete_one({"_id": ObjectId(mediafile_id)})
        return result.deleted_count

    def list_all(self):
        """List all media file documents."""
        mediafiles = list(self.db.find({}))
        return [self.to_dict(mediafile) for mediafile in mediafiles]
