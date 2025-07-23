import uuid
import json
import os
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from fins.config import DIR_MEDIA

# Ensure media directory exists
DIR_MEDIA.mkdir(parents=True, exist_ok=True)

class Media:
    def __init__(self):
        self._uuid = str(uuid.uuid4())
        # Auto-register on creation
        media_cache.register(self)
    def uuid(self) -> str:
        return self._uuid
    def handle(self) -> str:
        return f"[{self.__class__.__name__.lower()}:{self._uuid}]"

class Chart(Media):
    def __init__(self, image_bytes: bytes):
        self.image_bytes = image_bytes
        super().__init__()

class DataFrameMedia(Media):
    def __init__(self, df: pd.DataFrame):
        self.df = df
        super().__init__()
    def to_bytes(self) -> bytes:
        return self.df.to_json(orient='table').encode('utf-8')
    @staticmethod
    def from_bytes(data: bytes) -> 'DataFrameMedia':
        import io
        df = pd.read_json(io.BytesIO(data), orient='table')
        return DataFrameMedia(df)

class MediaCache:
    def __init__(self):
        # No in-memory cache - everything goes to disk
        pass
    
    def _get_media_path(self, uuid: str) -> Path:
        """Get path for media file"""
        return DIR_MEDIA / f"{uuid}.bin"
    
    def _get_metadata_path(self, uuid: str) -> Path:
        """Get path for metadata file"""
        return DIR_MEDIA / f"{uuid}.json"
    
    def register(self, media: Media):
        """Store media to disk"""
        uuid_str = media.uuid()
        
        # Store the media data
        media_path = self._get_media_path(uuid_str)
        if isinstance(media, Chart):
            with open(media_path, 'wb') as f:
                f.write(media.image_bytes)
        elif isinstance(media, DataFrameMedia):
            with open(media_path, 'wb') as f:
                f.write(media.to_bytes())
        
        # Store metadata
        metadata_path = self._get_metadata_path(uuid_str)
        metadata = {
            'type': media.__class__.__name__,
            'uuid': uuid_str,
            'handle': media.handle()
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
    
    def get(self, uuid: str) -> Optional[Media]:
        """Load media from disk"""
        media_path = self._get_media_path(uuid)
        metadata_path = self._get_metadata_path(uuid)
        
        if not media_path.exists() or not metadata_path.exists():
            return None
        
        try:
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Load media data based on type
            media_type = metadata.get('type')
            if media_type == 'Chart':
                with open(media_path, 'rb') as f:
                    image_bytes = f.read()
                return Chart(image_bytes)
            elif media_type == 'DataFrameMedia':
                with open(media_path, 'rb') as f:
                    data = f.read()
                return DataFrameMedia.from_bytes(data)
            else:
                # Unknown media type
                return None
                
        except Exception:
            return None
    
    def list_all(self) -> list[str]:
        """List all UUIDs in the cache"""
        uuids = set()
        for file in DIR_MEDIA.glob("*.json"):
            uuid_str = file.stem  # Remove .json extension
            uuids.add(uuid_str)
        return list(uuids)

media_cache = MediaCache()
