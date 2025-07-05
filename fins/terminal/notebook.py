"""
Terminal commands for the notebook system.
"""

from typing import Optional, List
from datetime import datetime

from fins.entities.note import Note as NoteEntity, Principle, Observation, Trade, Fact, Strategy, NoteSymbol
from fins.entities.basket import Basket
from fins.notebook import notebook
from fins.notebook.assistant import assistant


def NotePrinciple(content: str, title: Optional[str] = None, date: Optional[datetime] = None) -> Principle:
    """
    Create and save a principle note.
    
    Args:
        content: The content describing the principle
        title: The title of the principle (auto-generated if not provided)
        date: When the principle was formulated (defaults to now)
        
    Returns:
        The created Principle note
        
    Example:
        NotePrinciple("Don't buy stocks in free fall - wait for stabilization")
        NotePrinciple("Don't buy stocks in free fall", "Never catch falling knives")
    """
    if title is None:
        title = f"Principle #{datetime.now().strftime('%m%d-%H%M')}"
    
    return Principle(title=title, content=content, date=date).save()


def NoteObservation(content: str, title: Optional[str] = None, basket: Optional[Basket] = None, date: Optional[datetime] = None) -> Observation:
    """
    Create and save an observation note.
    
    Args:
        content: The content describing the observation
        title: The title of the observation (auto-generated if not provided)
        basket: Optional basket of related symbols
        date: When the observation was made (defaults to now)
        
    Returns:
        The created Observation note
        
    Example:
        NoteObservation("Major tech stocks down 5%+ on rate fears", basket=Screen(sector="Technology"))
        NoteObservation("Major tech stocks down 5%+ on rate fears", "Tech selloff")
    """
    if title is None:
        title = f"Observation #{datetime.now().strftime('%m%d-%H%M')}"
    
    baskets = {'main': basket} if basket else None
    return Observation(title=title, content=content, baskets=baskets, date=date).save()


def NoteTrade(content: str, title: Optional[str] = None, bought_basket: Optional[Basket] = None, 
              sold_basket: Optional[Basket] = None, status: str = "executed", 
              date: Optional[datetime] = None) -> Trade:
    """
    Create and save a trade note.
    
    Args:
        content: The content describing the trade
        title: The title of the trade (auto-generated if not provided)
        bought_basket: Basket of items bought
        sold_basket: Basket of items sold
        status: Trade status ("executed", "pending", "canceled")
        date: When the trade occurred (defaults to now)
        
    Returns:
        The created Trade note
        
    Example:
        NoteTrade("Bought AAPL on dip", bought_basket=Basket.from_tickers(["AAPL"]))
        NoteTrade("Bought AAPL on dip", "AAPL swing trade")
    """
    if title is None:
        title = f"Trade #{datetime.now().strftime('%m%d-%H%M')}"
    
    return Trade(
        title=title, 
        content=content, 
        bought_basket=bought_basket,
        sold_basket=sold_basket,
        status=status,
        date=date
    ).save()


def NoteFact(content: str, title: Optional[str] = None, source: Optional[str] = None, 
             confidence: float = 1.0, basket: Optional[Basket] = None, 
             date: Optional[datetime] = None) -> Fact:
    """
    Create and save a fact note.
    
    Args:
        content: The content describing the fact
        title: The title of the fact (auto-generated if not provided)
        source: The source of the fact
        confidence: Confidence level (0.0 to 1.0)
        basket: Optional basket of related symbols
        date: When the fact was recorded (defaults to now)
        
    Returns:
        The created Fact note
        
    Example:
        NoteFact("Elon Musk didn't found Tesla", source="Wikipedia", confidence=0.95)
        NoteFact("Elon Musk didn't found Tesla", "Tesla founding")
    """
    if title is None:
        title = f"Fact #{datetime.now().strftime('%m%d-%H%M')}"
    
    baskets = {'main': basket} if basket else None
    return Fact(
        title=title, 
        content=content, 
        source=source, 
        confidence=confidence,
        baskets=baskets,
        date=date
    ).save()


def NoteStrategy(content: str, title: Optional[str] = None, time_horizon: Optional[str] = None,
                 risk_level: Optional[str] = None, status: str = "active",
                 basket: Optional[Basket] = None, date: Optional[datetime] = None) -> Strategy:
    """
    Create and save a strategy note.
    
    Args:
        content: The content describing the strategy
        title: The title of the strategy (auto-generated if not provided)
        time_horizon: Time horizon ("short-term", "medium-term", "long-term")
        risk_level: Risk level ("low", "medium", "high")
        status: Strategy status ("active", "inactive", "completed")
        basket: Optional basket of related symbols
        date: When the strategy was created (defaults to now)
        
    Returns:
        The created Strategy note
        
    Example:
        NoteStrategy("Dollar cost average into QQQ", time_horizon="long-term", risk_level="medium")
        NoteStrategy("Dollar cost average into QQQ", "DCA tech")
    """
    if title is None:
        title = f"Strategy #{datetime.now().strftime('%m%d-%H%M')}"
    
    baskets = {'main': basket} if basket else None
    return Strategy(
        title=title,
        content=content,
        time_horizon=time_horizon,
        risk_level=risk_level,
        status=status,
        baskets=baskets,
        date=date
    ).save()


def NoteSymbolCmd(symbol, content: str, title: Optional[str] = None, date: Optional[datetime] = None):
    """
    Create and save a note on a specific symbol.
    
    Args:
        symbol: The ticker symbol (str), Symbol, or BasketItem
        content: The note content
        title: Optional title (auto-generated if not provided)
        date: When the note was created (defaults to now)
    Returns:
        The created NoteSymbol note
    Example:
        NoteSymbol('AAPL', 'Apple is overbought')
        NoteSymbol(AAPL, 'Apple is overbought')
    """
    return NoteSymbol(symbol, content, title=title, date=date).save()


def Notes(query: str = "", note_type: Optional[str] = None, limit: int = 10) -> List[NoteEntity]:
    """
    List or search notes.
    
    Args:
        query: Search query for title/content (empty string lists all)
        note_type: Filter by note type ("principle", "observation", "trade", "fact", "strategy")
        limit: Maximum number of results
        
    Returns:
        List of matching notes
        
    Examples:
        Notes()  # List recent 10 notes
        Notes("Tesla")  # Search for notes containing "Tesla"
        Notes(note_type="trade", limit=5)  # List recent 5 trades
    """
    notebook = notebook()
    
    if query:
        notes = notebook.search(query, note_type=note_type, limit=limit)
        print(f"Found {len(notes)} notes matching '{query}':")
    else:
        notes = notebook.list_notes(note_type=note_type, limit=limit, offset=0)
        type_desc = f" {note_type}" if note_type else ""
        print(f"Recent {len(notes)}{type_desc} notes:")
    
    for note in notes:
        symbols_info = ""
        if note.related_symbols:
            symbols_info = f" [{', '.join(note.related_symbols[:3])}{'...' if len(note.related_symbols) > 3 else ''}]"
        
        # Truncate content preview to 60 characters
        content_preview = note.content[:60] + "..." if len(note.content) > 60 else note.content
        content_preview = content_preview.replace('\n', ' ')  # Replace newlines with spaces
        
        print(f"  {note.id[:8]} | {note.date.strftime('%Y-%m-%d')} | {note.entity_type:12} | {note.title}")
        print(f"    {content_preview}{symbols_info}")
    
    return notes


def Note(note_id: str) -> Optional[NoteEntity]:
    """
    Get a note by ID (supports partial ID matching).
    
    Args:
        note_id: Full or partial note ID
        
    Returns:
        The note if found, None otherwise
        
    Example:
        Note("a1b2c3d4")  # Full ID
        Note("a1b2")      # Partial ID
    """
    notebook = notebook()
    
    # Try exact match first
    note = notebook.get(note_id)
    
    if note is None and len(note_id) < 36:
        # Try partial ID matching by listing all and finding match
        all_notes = notebook.list_notes(limit=1000)  # Get many notes for partial matching
        matches = [n for n in all_notes if n.id.startswith(note_id)]
        
        if len(matches) == 1:
            note = matches[0]
            print(f"Found note with partial ID '{note_id}': {note.id}")
        elif len(matches) > 1:
            print(f"Multiple notes match '{note_id}':")
            for match in matches[:5]:  # Show first 5 matches
                print(f"  {match.id} | {match.title}")
            return None
    
    if note:
        print(f"Note: {note.title}")
        print(f"Type: {note.entity_type}")
        print(f"Date: {note.date}")
        print(f"Content: {note.content}")
        
        if note.related_symbols:
            print(f"Related symbols: {', '.join(note.related_symbols)}")
        
        # Show type-specific info
        if hasattr(note, 'status'):
            print(f"Status: {note.status}")
        if hasattr(note, 'sources') and note.sources:
            print(f"Sources: {', '.join(note.sources)}")
        if hasattr(note, 'confidence'):
            print(f"Confidence: {note.confidence}")
        if hasattr(note, 'time_horizon'):
            print(f"Time horizon: {note.time_horizon}")
        if hasattr(note, 'risk_level'):
            print(f"Risk level: {note.risk_level}")
        
        return note
    else:
        print(f"Note not found: {note_id}")
        return None


def AiSync():
    """
    Sync all notes to the OpenAI assistant using file search.
    
    Args:
        force: If True, re-upload all notes even if already uploaded
        
    Example:
        AiSync()  # Sync all notes
        AiSync(force=True)  # Force re-upload
    """
    try:
        assistant().sync_notes()
    except Exception as e:
        print(f"✗ Failed to sync notes: {e}")


def Ai(message: str):
    """
    Ask a question to the OpenAI assistant.
    
    Args:
        message: The question or message to send
        
    Example:
        Ai("What are my recent observations about tech stocks?")
        Ai("Show me all trades involving AAPL")
    """
    try:
        assistant = assistant()
        response = assistant.ask(message)
        print(f"\nAssistant: {response}")
    except Exception as e:
        print(f"✗ Failed to get assistant response: {e}")


def AiStatus():
    """
    Show the status of the OpenAI assistant.
    
    Example:
        AiStatus()
    """
    try:
        assistant = assistant()
        status = assistant.get_status()
        
        if status.get('status') == 'error':
            print(f"✗ Assistant error: {status.get('error')}")
            return
        
        print("Assistant Status:")
        print(f"  ID: {status.get('assistant_id', 'N/A')}")
        print(f"  Name: {status.get('name', 'N/A')}")
        print(f"  Model: {status.get('model', 'N/A')}")
        print(f"  Created: {status.get('created_at', 'N/A')}")
        print(f"  Updated: {status.get('last_updated', 'N/A')}")
        print(f"  New notes this session: {status.get('new_notes_count', 0)}")
        print(f"  Sync threshold: {status.get('sync_threshold', 10)}")
        
    except Exception as e:
        print(f"✗ Failed to get assistant status: {e}")


 