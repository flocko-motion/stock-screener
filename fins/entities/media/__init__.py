import uuid
from typing import Dict

class Media:
    def __init__(self):
        self._uuid = str(uuid.uuid4())
    def uuid(self) -> str:
        return self._uuid
    def handle(self) -> str:
        return f"{self.__class__.__name__.lower()}:{self._uuid}"

class Chart(Media):
    def __init__(self, image_bytes: bytes):
        super().__init__()
        self.image_bytes = image_bytes

class MediaCache:
    def __init__(self):
        self._cache: Dict[str, Media] = {}
    def register(self, media: Media):
        self._cache[media.uuid()] = media
    def get(self, uuid: str):
        return self._cache.get(uuid)

media_cache = MediaCache()
