"""
Note Entity

This module defines the Note class and its subclasses for different types of notes
in the FINS system.
"""

from typing import Dict, Any, Optional, List, ClassVar, Union
from datetime import datetime

from .entity import Entity
from .basket import Basket


class Note(Entity):
    """
    Base class for all note entities in the FINS system.
    
    Attributes:
        title (str): The title of the note
        content (str): The content of the note
        date (datetime): When the note was created or when the event occurred
        baskets (Dict[str, Basket]): Dictionary of named baskets embedded in this note
    """
    
    entity_type: ClassVar[str] = "note"
    storage_dir: ClassVar[str] = "notes"
    
    def __init__(self, 
                 title: str, 
                 content: str,
                 date: Optional[datetime] = None,
                 baskets: Optional[Dict[str, Basket]] = None,
                 id: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a note.
        
        Args:
            title: The title of the note
            content: The content of the note
            date: When the note was created or when the event occurred
            baskets: Dictionary of named baskets embedded in this note
            id: Unique identifier (generated if not provided)
            created_at: Creation timestamp (current time if not provided)
            updated_at: Update timestamp (same as created_at if not provided)
            tags: List of tags (empty list if not provided)
            metadata: Additional metadata (empty dict if not provided)
        """
        super().__init__(id, created_at, updated_at, tags, metadata)
        self._title = title
        self._content = content
        self._date = date or datetime.now()
        self._baskets = baskets or {}
    
    @property
    def title(self) -> str:
        """Get the title of the note."""
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        """Set the title of the note."""
        self._title = value
        self.update()
    
    @property
    def content(self) -> str:
        """Get the content of the note."""
        return self._content
    
    @content.setter
    def content(self, value: str) -> None:
        """Set the content of the note."""
        self._content = value
        self.update()
    
    @property
    def date(self) -> datetime:
        """Get the date of the note."""
        return self._date
    
    @date.setter
    def date(self, value: datetime) -> None:
        """Set the date of the note."""
        self._date = value
        self.update()
    
    @property
    def baskets(self) -> Dict[str, Basket]:
        """Get all baskets (backward compatibility property)."""
        return self._baskets
    
    def basket(self, *args) -> Union[Dict[str, Basket], Optional[Basket], 'Note']:
        """
        Get, set, or remove baskets (getter/setter combined).
        
        Args:
            No args: Return all baskets
            One arg (name): Return specific basket
            Two args (name, basket): Set basket (basket can be None to remove)
            
        Returns:
            - No args: Dict of all baskets
            - One arg: The specific basket or None if not found
            - Two args: Self for chaining after setting/removing
            
        Examples:
            note.basket()  # Get all baskets
            note.basket("main")  # Get basket named "main"
            note.basket("main", my_basket)  # Set basket named "main"
            note.basket("main", None)  # Remove basket named "main"
        """
        if len(args) == 0:
            # No args: return all baskets
            return self._baskets
        elif len(args) == 1:
            # One arg: get specific basket
            name = args[0]
            return self._baskets.get(name)
        elif len(args) == 2:
            # Two args: set or remove basket
            name, basket = args
            if basket is None:
                # Remove basket
                if name in self._baskets:
                    del self._baskets[name]
                    self.update()
            else:
                # Set basket
                self._baskets[name] = basket
                self.update()
            return self
        else:
            raise ValueError("basket() takes 0, 1, or 2 arguments")
    
    @property
    def related_symbols(self) -> List[str]:
        """
        Get a list of ticker symbols related to this note by extracting them from all baskets.
        
        Returns:
            List of ticker symbols
        """
        symbols = []
        for basket in self._baskets.values():
            for item in basket._items:
                if item.symbol.ticker not in symbols:
                    symbols.append(item.symbol.ticker)
        return symbols
    
    def tag(self, tag_name: str) -> 'Note':
        """
        Add a tag to the note (chainable).
        
        Args:
            tag_name: The tag to add
            
        Returns:
            Self for chaining
            
        Example:
            NoteFact("Elon is a racist").tag("fyi").tag("controversial")
        """
        if tag_name not in self.tags:
            self.tags.append(tag_name)
            self.save()
        return self
    

    
    def save(self) -> 'Note':
        """Save the note to the notebook."""
        from fins.notebook import get_notebook
        notebook = get_notebook()
        
        if notebook.save(self):
            print(f"✓ Saved {self.entity_type}: {self.title}")
        else:
            print(f"✗ Failed to save {self.entity_type}: {self.title}")
        
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the note to a dictionary.
        
        Returns:
            A dictionary representation of the note
        """
        data = super().to_dict()
        baskets_dict = {}
        for name, basket in self._baskets.items():
            baskets_dict[name] = basket.to_dict()
            
        data.update({
            "title": self._title,
            "content": self._content,
            "date": self._date.isoformat(),
            "baskets": baskets_dict
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """
        Create a note from a dictionary.
        
        Args:
            data: The dictionary containing note data
            
        Returns:
            A new Note instance
        """
        # Parse note-specific timestamps
        date = datetime.fromisoformat(data.get('date')) if data.get('date') else None
        
        # Parse baskets
        baskets = {}
        from .basket import Basket
        
        if isinstance(data.get('baskets'), dict):
            for name, basket_data in data.get('baskets', {}).items():
                if isinstance(basket_data, dict):
                    basket = Basket.from_dict(basket_data)
                    baskets[name] = basket
        
        # Create a copy of data with parsed values for Note-specific fields
        note_data = data.copy()
        note_data.update({
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'date': date,
            'baskets': baskets
        })
        
        # Let Entity.from_dict handle the common fields
        return super().from_dict(note_data)


class Principle(Note):
    """
    A principle note, representing a guiding principle or rule.
    
    Principles are philosophical rules that should be followed in investing or trading.
    They don't typically reference specific baskets or trades.
    """
    entity_type: ClassVar[str] = "principle"


class Observation(Note):
    """
    An observation note, representing a market or data observation.
    
    Observations are quick notes taken while reading news or analyzing markets.
    They can reference specific baskets for context.
    """
    entity_type: ClassVar[str] = "observation"


class Trade(Note):
    """
    A trade note, representing a buy/sell action taken.
    
    Trades record actual market actions with associated baskets for what was bought and sold.
    All monetary values are normalized to USD as the unit of account.
    
    Attributes:
        status (str): The status of the trade (executed, pending, canceled)
    """
    entity_type: ClassVar[str] = "trade"
    
    def __init__(self, 
                 title: str, 
                 content: str,
                 bought_basket: Optional[Basket] = None,
                 sold_basket: Optional[Basket] = None,
                 status: str = "executed",
                 date: Optional[datetime] = None,
                 baskets: Optional[Dict[str, Basket]] = None,
                 **kwargs):
        """
        Initialize a trade note.
        
        Args:
            title: The title of the note
            content: The content of the note
            bought_basket: Basket of items that were bought
            sold_basket: Basket of items that were sold
            status: The status of the trade (executed, pending, canceled)
            date: When the trade occurred
            baskets: Additional named baskets beyond bought/sold
            **kwargs: Additional arguments passed to the parent class
        """
        # Initialize baskets dictionary
        trade_baskets = baskets or {}
        
        # Add bought and sold baskets
        if bought_basket:
            trade_baskets["bought"] = bought_basket
        elif "bought" not in trade_baskets:
            trade_baskets["bought"] = Basket(name="Bought")
            
        if sold_basket:
            trade_baskets["sold"] = sold_basket
        elif "sold" not in trade_baskets:
            trade_baskets["sold"] = Basket(name="Sold")
        
        super().__init__(title, content, date, trade_baskets, **kwargs)
        self._status = status
    
    @property
    def status(self) -> str:
        """Get the status of the trade."""
        return self._status
    
    @status.setter
    def status(self, value: str) -> None:
        """Set the status of the trade."""
        self._status = value
        self.update()
    
    @property
    def bought_basket(self) -> Basket:
        """
        Get the basket of bought items.
        
        Returns:
            The bought basket
        """
        return self._baskets.get("bought", Basket(name="Bought"))
    
    @bought_basket.setter
    def bought_basket(self, basket: Basket) -> None:
        """
        Set the basket of bought items.
        
        Args:
            basket: The new bought basket
        """
        self._baskets["bought"] = basket
        self.update()
    
    @property
    def sold_basket(self) -> Basket:
        """
        Get the basket of sold items.
        
        Returns:
            The sold basket
        """
        return self._baskets.get("sold", Basket(name="Sold"))
    
    @sold_basket.setter
    def sold_basket(self, basket: Basket) -> None:
        """
        Set the basket of sold items.
        
        Args:
            basket: The new sold basket
        """
        self._baskets["sold"] = basket
        self.update()
    
    @property
    def bought_value_usd(self) -> float:
        """
        Calculate the total USD value of bought items.
        
        Returns:
            The total USD value
        """
        total = 0.0
        for item in self.bought_basket._items:
            price = item.symbol.get_data('price', 0.0)
            total += item.amount * price
        return total
    
    @property
    def sold_value_usd(self) -> float:
        """
        Calculate the total USD value of sold items.
        
        Returns:
            The total USD value
        """
        total = 0.0
        for item in self.sold_basket._items:
            price = item.symbol.get_data('price', 0.0)
            total += item.amount * price
        return total
    
    @property
    def net_value_usd(self) -> float:
        """
        Calculate the net USD value of the trade (sold - bought).
        
        Returns:
            The net USD value
        """
        return self.sold_value_usd - self.bought_value_usd
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the trade note to a dictionary.
        
        Returns:
            A dictionary representation of the trade note
        """
        data = super().to_dict()
        data.update({
            "status": self._status
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """
        Create a trade note from a dictionary.
        
        Args:
            data: The dictionary containing trade note data
            
        Returns:
            A new Trade instance
        """
        # Handle legacy format with separate bought_basket and sold_basket fields
        from .basket import Basket
        baskets = {}
        
        if isinstance(data.get('baskets'), dict):
            for name, basket_data in data.get('baskets', {}).items():
                if isinstance(basket_data, dict):
                    basket = Basket.from_dict(basket_data)
                    baskets[name] = basket
        
        if data.get('bought_basket') and isinstance(data['bought_basket'], dict):
            bought_basket = Basket.from_dict(data['bought_basket'])
            baskets["bought"] = bought_basket
        
        if data.get('sold_basket') and isinstance(data['sold_basket'], dict):
            sold_basket = Basket.from_dict(data['sold_basket'])
            baskets["sold"] = sold_basket
        
        # Create a copy of data with trade-specific fields
        trade_data = data.copy()
        trade_data.update({
            'status': data.get('status', 'executed'),
            'baskets': baskets
        })
        
        # Let Note.from_dict handle Note and Entity fields
        return super().from_dict(trade_data)


class Fact(Note):
    """
    A fact note, representing a piece of factual information.
    
    Facts are pieces of information that are considered true and may be useful
    for future reference, such as "Elon Musk didn't found Tesla."
    
    Attributes:
        source (str): The source of the fact
        confidence (float): Confidence level in the fact (0.0 to 1.0)
    """
    entity_type: ClassVar[str] = "fact"
    
    def __init__(self, 
                 title: str, 
                 content: str,
                 source: Optional[str] = None,
                 confidence: float = 1.0,
                 date: Optional[datetime] = None,
                 baskets: Optional[Dict[str, Basket]] = None,
                 **kwargs):
        """
        Initialize a fact note.
        
        Args:
            title: The title of the note
            content: The content of the note
            source: The initial source of the fact (optional)
            confidence: Confidence level in the fact (0.0 to 1.0)
            date: When the fact was recorded
            baskets: Dictionary of named baskets related to this fact
            **kwargs: Additional arguments passed to the parent class
        """
        super().__init__(title, content, date, baskets, **kwargs)
        self._sources = [source] if source else []
        self._confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
    
    @property
    def confidence(self) -> float:
        """Get the confidence level of the fact."""
        return self._confidence
    
    @confidence.setter
    def confidence(self, value: float) -> None:
        """Set the confidence level of the fact."""
        self._confidence = max(0.0, min(1.0, value))  # Clamp between 0 and 1
        self.update()
    
    @property 
    def sources(self) -> List[str]:
        """Get all sources (always a list)."""
        return self._sources
    
    def source(self, source_value: str) -> 'Fact':
        """
        Add a source to the fact (chainable).
        
        Args:
            source_value: The source to add
            
        Returns:
            Self for chaining
            
        Example:
            NoteFact("Elon didn't found Tesla").source("Wikipedia").source("TechCrunch")
        """
        if source_value not in self._sources:
            self._sources.append(source_value)
            self.save()
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the fact note to a dictionary.
        
        Returns:
            A dictionary representation of the fact note
        """
        data = super().to_dict()
        data.update({
            "sources": self._sources,
            "confidence": self._confidence
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fact':
        """
        Create a fact note from a dictionary.
        
        Args:
            data: The dictionary containing fact note data
            
        Returns:
            A new Fact instance
        """
        # Handle backwards compatibility - convert old 'source' field to 'sources' list
        sources = data.get('sources', [])
        if not sources and data.get('source'):
            sources = [data.get('source')]
        
        # Create a copy of data with fact-specific fields
        fact_data = data.copy()
        fact_data.update({
            'source': sources[0] if sources else None,  # Pass first source as 'source' parameter
            'confidence': data.get('confidence', 1.0)
        })
        
        # Let Note.from_dict handle Note and Entity fields
        return super().from_dict(fact_data)


class Strategy(Note):
    """
    A strategy note, representing a trading or investment strategy.
    
    Strategies are plans that could be followed, potentially with associated baskets.
    
    Attributes:
        time_horizon (str): The time horizon for the strategy (e.g., "short-term", "long-term")
        risk_level (str): The risk level of the strategy (e.g., "low", "medium", "high")
        status (str): The status of the strategy (e.g., "active", "inactive", "completed")
    """
    entity_type: ClassVar[str] = "strategy"
    
    def __init__(self, 
                 title: str, 
                 content: str,
                 time_horizon: Optional[str] = None,
                 risk_level: Optional[str] = None,
                 status: str = "active",
                 date: Optional[datetime] = None,
                 baskets: Optional[Dict[str, Basket]] = None,
                 **kwargs):
        """
        Initialize a strategy note.
        
        Args:
            title: The title of the note
            content: The content of the note
            time_horizon: The time horizon for the strategy (e.g., "short-term", "long-term")
            risk_level: The risk level of the strategy (e.g., "low", "medium", "high")
            status: The status of the strategy (e.g., "active", "inactive", "completed")
            date: When the strategy was created
            baskets: Dictionary of named baskets related to this strategy
            **kwargs: Additional arguments passed to the parent class
        """
        super().__init__(title, content, date, baskets, **kwargs)
        self._time_horizon = time_horizon
        self._risk_level = risk_level
        self._status = status
    
    @property
    def time_horizon(self) -> Optional[str]:
        """Get the time horizon of the strategy."""
        return self._time_horizon
    
    @time_horizon.setter
    def time_horizon(self, value: Optional[str]) -> None:
        """Set the time horizon of the strategy."""
        self._time_horizon = value
        self.update()
    
    @property
    def risk_level(self) -> Optional[str]:
        """Get the risk level of the strategy."""
        return self._risk_level
    
    @risk_level.setter
    def risk_level(self, value: Optional[str]) -> None:
        """Set the risk level of the strategy."""
        self._risk_level = value
        self.update()
    
    @property
    def status(self) -> str:
        """Get the status of the strategy."""
        return self._status
    
    @status.setter
    def status(self, value: str) -> None:
        """Set the status of the strategy."""
        self._status = value
        self.update()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the strategy note to a dictionary.
        
        Returns:
            A dictionary representation of the strategy note
        """
        data = super().to_dict()
        data.update({
            "time_horizon": self._time_horizon,
            "risk_level": self._risk_level,
            "status": self._status
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """
        Create a strategy note from a dictionary.
        
        Args:
            data: The dictionary containing strategy note data
            
        Returns:
            A new Strategy instance
        """
        # Create a copy of data with strategy-specific fields
        strategy_data = data.copy()
        strategy_data.update({
            'time_horizon': data.get('time_horizon'),
            'risk_level': data.get('risk_level'),
            'status': data.get('status', 'active')
        })
        
        # Let Note.from_dict handle Note and Entity fields
        return super().from_dict(strategy_data) 


class NoteSymbol(Note):
    """
    A note on a specific symbol (ticker).
    
    Attributes:
        _symbol (str): The ticker symbol this note refers to.
    """
    entity_type: ClassVar[str] = "symbol_note"

    def __init__(self, symbol, content: str, title: Optional[str] = None, date: Optional[datetime] = None, baskets: Optional[Dict[str, Basket]] = None, **kwargs):
        """
        Initialize a symbol note.
        
        Args:
            symbol: The ticker symbol (str), Symbol, or BasketItem
            content: The note content
            title: Optional title (auto-generated if not provided)
            date: When the note was created
            baskets: Optional baskets
            **kwargs: Additional args
        """
        # Accept str, Symbol, or BasketItem for symbol
        ticker = None
        if hasattr(symbol, 'ticker'):
            ticker = symbol.ticker
        elif hasattr(symbol, 'symbol'):
            ticker = symbol.symbol
        else:
            ticker = str(symbol)
        self._symbol = ticker
        if not title:
            title = f"Note on {self._symbol}"
        super().__init__(title, content, date, baskets, **kwargs)

    def symbol(self, value=None):
        """
        Get or set the symbol (ticker) for this note.
        
        Args:
            value: If provided, sets the symbol (str, Symbol, or BasketItem)
        Returns:
            The current symbol (ticker as str) if no value is given, else self for chaining
        """
        if value is None:
            return self._symbol
        # Accept str, Symbol, or BasketItem
        if hasattr(value, 'ticker'):
            self._symbol = value.ticker
        elif hasattr(value, 'symbol'):
            self._symbol = value.symbol
        else:
            self._symbol = str(value)
        self.update()
        return self

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['symbol'] = self._symbol
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoteSymbol':
        symbol = data.get('symbol')
        content = data.get('content', '')
        title = data.get('title')
        date = datetime.fromisoformat(data['date']) if data.get('date') else None
        baskets = None
        if isinstance(data.get('baskets'), dict):
            from .basket import Basket
            baskets = {name: Basket.from_dict(b) for name, b in data['baskets'].items()}
        return cls(symbol, content, title=title, date=date, baskets=baskets, **data) 