"""
PostgreSQL-based notebook for storing notes using SQLAlchemy.
"""

import json
from datetime import datetime
from typing import List, Optional, Any, ClassVar

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship

from fins.database import session_scope, Base
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
    """PostgreSQL-based notebook for storing notes using SQLAlchemy."""

    test_mode = False

    def __init__(self):
        pass

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
            with session_scope() as session:
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
                    existing.type = note.__class__.__name__
                    existing.title = note.title()
                    existing.content = note.content()
                    existing.date = note.date()
                    existing.data = json.dumps(data)
                else:
                    # Create new note
                    new_note = NoteModel(
                        id=note.id,
                        type=note.__class__.__name__,
                        title=note.title(),
                        content=note.content(),
                        date=note.date(),
                        data=json.dumps(data)
                    )
                    session.add(new_note)
                
                return True
                
        except Exception as e:
            print(f"Error saving note: {e}")
            return False

    def load(self, note_id: str) -> Optional[Note]:
        """
        Load a note from the database.
        
        Args:
            note_id: The ID of the note to load
            
        Returns:
            The note if found, None otherwise
        """
        try:
            with session_scope() as session:
                note_model = session.query(NoteModel).filter_by(id=note_id).first()
                
                if not note_model:
                    return None
                
                # Parse the data blob
                data = json.loads(note_model.data) if note_model.data else {}
                
                # Create the appropriate note type
                note_class = globals().get(note_model.type, Note)
                
                # Extract basic fields
                kwargs = {
                    'id': note_model.id,
                    'title': note_model.title,
                    'content': note_model.content,
                    'date': note_model.date,
                    'symbol': data.get('symbol'),
                    'created_at': datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
                    'updated_at': datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
                    'tags': data.get('tags', []),
                    'metadata': data.get('metadata', {}),
                    'vector_store_id': data.get('vector_store_id')
                }
                
                # Add type-specific fields
                if note_model.type in ['Trade', 'Strategy']:
                    kwargs['status'] = data.get('status')
                if note_model.type == 'Fact':
                    kwargs['sources'] = data.get('sources', [])
                    kwargs['confidence'] = data.get('confidence')
                if note_model.type == 'Strategy':
                    kwargs['time_horizon'] = data.get('time_horizon')
                    kwargs['risk_level'] = data.get('risk_level')
                
                # Create baskets if present
                baskets = {}
                for name, basket_data in data.get('baskets', {}).items():
                    baskets[name] = Basket.from_dict(basket_data)
                kwargs['baskets'] = baskets
                
                return note_class(**kwargs)
                
        except Exception as e:
            print(f"Error loading note: {e}")
            return None

    def list_notes(self, limit: Optional[int] = None) -> List[Note]:
        """
        List all notes in the database.
        
        Args:
            limit: Maximum number of notes to return
            
        Returns:
            List of notes
        """
        try:
            with session_scope() as session:
                query = session.query(NoteModel).order_by(NoteModel.date.desc())
                
                if limit:
                    query = query.limit(limit)
                
                note_models = query.all()
                notes = []
                
                for note_model in note_models:
                    note = self.load(note_model.id)
                    if note:
                        notes.append(note)
                
                return notes
                
        except Exception as e:
            print(f"Error listing notes: {e}")
            return []

    def delete(self, note_id: str) -> bool:
        """
        Delete a note from the database.
        
        Args:
            note_id: The ID of the note to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with session_scope() as session:
                result = session.query(NoteModel).filter_by(id=note_id).delete()
                return result > 0
                
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False

    def count(self) -> int:
        """
        Get the number of notes in the database.
        
        Returns:
            The number of notes
        """
        try:
            with session_scope() as session:
                return session.query(NoteModel).count()
        except Exception as e:
            print(f"Error counting notes: {e}")
            return 0

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
            with session_scope() as session:
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

