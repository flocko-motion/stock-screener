"""
SQLite-based notebook for storing notes using SQLAlchemy.
"""

import json
from datetime import datetime
from typing import List, Optional, Any, ClassVar

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship

from fins.database import Base, session_scope, init_db
from fins.entities.note import Note, Principle, Observation, Trade, Fact, Strategy, NoteSymbol
from fins.entities.basket import Basket


class NoteModel(Base):
    """SQLAlchemy model for note data."""
    
    __tablename__ = 'notes'
    
    id = Column(String(36), primary_key=True)
    type = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    data = Column(Text, nullable=True)  # JSON blob for all additional fields


class Notebook:
    """SQLite-based notebook for storing notes using the existing SQLAlchemy pattern."""

    test_mode = False

    def __init__(self, db_name: str = "notebook"):
        self.db_name = db_name
        # Initialize the database
        init_db(db_name, make_backup=db_name == "notebook")

    @classmethod
    def is_test_mode(cls):
        return cls.test_mode

    def save(self, note: Note) -> bool:
        """
        Save a note to the database.
        
        Args:
            note: The note to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with session_scope(self.db_name) as session:
                # Prepare the data blob with all additional fields
                data = {
                    'tags': note.tags,
                    'metadata': note.metadata,
                    'created_at': note.created_at.isoformat(),
                    'updated_at': note.updated_at.isoformat(),
                    'baskets': {name: basket.to_dict() for name, basket in note.basket().items()},
                    'vector_store_id': note.vector_store_file_id,
                    'symbol': note.symbol
                }
                
                # Add type-specific fields
                if isinstance(note, (Trade, Strategy)):
                    data['status'] = note.status
                if isinstance(note, Fact):
                    data['sources'] = note._sources
                    data['confidence'] = note.confidence
                if isinstance(note, Strategy):
                    data['time_horizon'] = note.time_horizon
                    data['risk_level'] = note.risk_level
                
                # Check if note already exists
                existing = session.query(NoteModel).filter_by(id=note.id).first()
                
                if existing:
                    # Update existing note
                    existing.type = note.entity_type
                    existing.title = note.title
                    existing.content = note.content
                    existing.date = note.date
                    existing.data = json.dumps(data)
                else:
                    # Create new note
                    note_model = NoteModel(
                        id=note.id,
                        type=note.entity_type,
                        title=note.title,
                        content=note.content,
                        date=note.date,
                        data=json.dumps(data)
                    )
                    session.add(note_model)
                
                return True
                
        except Exception as e:
            print(f"Error saving note: {e}")
            return False
    
    def get(self, note_id: str) -> Optional[Note]:
        """
        Get a note by ID.
        
        Args:
            note_id: The note ID
            
        Returns:
            The note if found, None otherwise
        """
        try:
            with session_scope(self.db_name) as session:
                note_model = session.query(NoteModel).filter_by(id=note_id).first()
                
                if note_model:
                    session.expunge(note_model)  # Detach from session
                    return self._model_to_note(note_model)
                return None
                
        except Exception as e:
            print(f"Error getting note: {e}")
            return None
    
    def list_notes(self, note_type: Optional[str] = None, limit: int = 50, offset: int = 0, full_text_search: Optional[str] = None) -> List[Note]:
        """
        List notes with optional filtering.
        
        Args:
            note_type: Filter by note type (e.g., "trade", "fact")
            limit: Maximum number of notes to return
            offset: Number of notes to skip
            full_text_search: Optional text to search in title and content
            
        Returns:
            List of notes
        """
        try:
            with session_scope(self.db_name) as session:
                query = session.query(NoteModel)
                
                if note_type:
                    query = query.filter(NoteModel.type == note_type)
                
                if full_text_search:
                    query = query.filter(
                        (NoteModel.title.like(f"%{full_text_search}%")) | 
                        (NoteModel.content.like(f"%{full_text_search}%"))
                    )
                
                note_models = query.order_by(NoteModel.date.desc()).limit(limit).offset(offset).all()
                
                # Detach from session
                for model in note_models:
                    session.expunge(model)
                
                return [self._model_to_note(model) for model in note_models]
                
        except Exception as e:
            print(f"Error listing notes: {e}")
            raise e
            # return []
    
    def search(self, query: str, note_type: Optional[str] = None, limit: int = 50) -> List[Note]:
        """
        Search notes by title and content.
        
        Args:
            query: Search query
            note_type: Filter by note type
            limit: Maximum number of results
            
        Returns:
            List of matching notes
        """
        try:
            with session_scope(self.db_name) as session:
                db_query = session.query(NoteModel).filter(
                    (NoteModel.title.like(f"%{query}%")) | 
                    (NoteModel.content.like(f"%{query}%"))
                )
                
                if note_type:
                    db_query = db_query.filter(NoteModel.type == note_type)
                
                note_models = db_query.order_by(NoteModel.date.desc()).limit(limit).all()
                
                # Detach from session
                for model in note_models:
                    session.expunge(model)
                
                return [self._model_to_note(model) for model in note_models]
                
        except Exception as e:
            print(f"Error searching notes: {e}")
            return []
    
    def delete(self, note_id: str) -> bool:
        """
        Delete a note by ID.
        
        Args:
            note_id: The note ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with session_scope(self.db_name) as session:
                result = session.query(NoteModel).filter_by(id=note_id).delete()
                return result > 0
                
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Delete all notes from the notebook.
        
        Returns:
            True if successful, False otherwise
        """
        if self.db_name != "notebook_test":
            print("⚠ Clearing all notes is not allowed in production database")
            return False

        print("Clearing all notes from DB..")
        try:
            with session_scope(self.db_name) as session:
                # First, let's check how many notes exist
                count_before = session.query(NoteModel).count()
                print(f"Found {count_before} notes to delete")
                
                if count_before == 0:
                    print("✓ No notes to delete")
                    return True
                
                # Delete all notes
                result = session.query(NoteModel).delete()
                session.flush()  # Ensure the delete is processed
                
                # Verify deletion
                count_after = session.query(NoteModel).count()
                print(f"✓ Deleted {result} notes from notebook (before: {count_before}, after: {count_after})")
                
                if count_after > 0:
                    print(f"⚠ Warning: {count_after} notes still remain after deletion")
                    return False
                
                return True
                
        except Exception as e:
            print(f"Error clearing all notes: {e}")
            return False
    
    def _model_to_note(self, model: NoteModel) -> Note:
        """Convert a NoteModel to a Note object."""
        # Parse the data JSON blob
        data = json.loads(model.data) if model.data else {}
        
        # Extract common fields
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        created_at = datetime.fromisoformat(data.get('created_at', model.date.isoformat()))
        updated_at = datetime.fromisoformat(data.get('updated_at', model.date.isoformat()))
        vector_store_id = data.get('vector_store_id')
        
        # Reconstruct baskets
        baskets = {}
        baskets_data = data.get('baskets', {})
        for name, basket_data in baskets_data.items():
            baskets[name] = Basket.from_dict(basket_data)
        
        # Common kwargs for all note types
        common_kwargs = {
            'title': model.title,
            'content': model.content,
            'date': model.date,
            'baskets': baskets,
            'id': model.id,
            'created_at': created_at,
            'updated_at': updated_at,
            'tags': tags,
            'metadata': metadata,
            'vector_store_id': vector_store_id,
            'symbol': data.get('symbol')
        }
        
        # Handle Fact sources (backward compatibility)
        fact_source = None
        if data.get('sources'):
            fact_source = data['sources'][0] if data['sources'] else None
        elif data.get('source'):
            fact_source = data['source']
        
        # Type-specific kwargs and classes
        type_configs = {
            'principle': (Principle, {}),
            'observation': (Observation, {}),
            'trade': (Trade, {'status': data.get('status', 'executed')}),
            'fact': (Fact, {
                'source': fact_source,
                'confidence': data.get('confidence', 1.0)
            }),
            'strategy': (Strategy, {
                'time_horizon': data.get('time_horizon'),
                'risk_level': data.get('risk_level'),
                'status': data.get('status', 'active')
            }),
            'symbol_note': (NoteSymbol, {})
        }
        
        # Get class and specific kwargs, default to base Note class
        note_class, specific_kwargs = type_configs.get(model.type, (Note, {}))
        
        # Merge common and specific kwargs
        all_kwargs = {**common_kwargs, **specific_kwargs}
        
        return note_class(**all_kwargs)


# Global notebook instance
_notebook = None
_notebook_test = None


def notebook() -> Notebook:
    if Notebook.test_mode:
        global _notebook_test
        if _notebook_test is None:
            _notebook_test = Notebook(db_name="notebook_test")
        return _notebook_test

    global _notebook
    if _notebook is None:
        _notebook = Notebook()
    return _notebook

