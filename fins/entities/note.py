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
        self.title = title
        self.content = content
        self.date = date or datetime.now()
        self.baskets = baskets or {}
    
    def add_basket(self, name: str, basket: Basket) -> None:
        """
        Add a basket to the note with the specified name.
        
        Args:
            name: The name to associate with the basket
            basket: The basket to add
        """
        self.baskets[name] = basket
        self.update()
    
    def get_basket(self, name: str) -> Optional[Basket]:
        """
        Get a basket by name.
        
        Args:
            name: The name of the basket to retrieve
            
        Returns:
            The basket if found, None otherwise
        """
        return self.baskets.get(name)
    
    def remove_basket(self, name: str) -> bool:
        """
        Remove a basket by name.
        
        Args:
            name: The name of the basket to remove
            
        Returns:
            True if the basket was removed, False if it wasn't found
        """
        if name in self.baskets:
            del self.baskets[name]
            self.update()
            return True
        return False
    
    @property
    def related_symbols(self) -> List[str]:
        """
        Get a list of ticker symbols related to this note by extracting them from all baskets.
        
        Returns:
            List of ticker symbols
        """
        symbols = []
        for basket in self.baskets.values():
            for item in basket.items:
                if item.symbol.ticker not in symbols:
                    symbols.append(item.symbol.ticker)
        return symbols
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the note to a dictionary.
        
        Returns:
            A dictionary representation of the note
        """
        data = super().to_dict()
        baskets_dict = {}
        for name, basket in self.baskets.items():
            baskets_dict[name] = basket.to_dict()
            
        data.update({
            "title": self.title,
            "content": self.content,
            "date": self.date.isoformat(),
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
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        date = datetime.fromisoformat(data.get('date')) if data.get('date') else None
        
        # Parse baskets
        baskets = {}
        from .basket import Basket
        
        if isinstance(data.get('baskets'), dict):
            for name, basket_data in data.get('baskets', {}).items():
                if isinstance(basket_data, dict):
                    basket = Basket.from_dict(basket_data)
                    baskets[name] = basket
        
        return cls(
            title=data.get('title', ''),
            content=data.get('content', ''),
            date=date,
            baskets=baskets,
            id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


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
        self.status = status
    
    @property
    def bought_basket(self) -> Basket:
        """
        Get the basket of bought items.
        
        Returns:
            The bought basket
        """
        return self.baskets.get("bought", Basket(name="Bought"))
    
    @bought_basket.setter
    def bought_basket(self, basket: Basket) -> None:
        """
        Set the basket of bought items.
        
        Args:
            basket: The new bought basket
        """
        self.baskets["bought"] = basket
        self.update()
    
    @property
    def sold_basket(self) -> Basket:
        """
        Get the basket of sold items.
        
        Returns:
            The sold basket
        """
        return self.baskets.get("sold", Basket(name="Sold"))
    
    @sold_basket.setter
    def sold_basket(self, basket: Basket) -> None:
        """
        Set the basket of sold items.
        
        Args:
            basket: The new sold basket
        """
        self.baskets["sold"] = basket
        self.update()
    
    @property
    def bought_value_usd(self) -> float:
        """
        Calculate the total USD value of bought items.
        
        Returns:
            The total USD value
        """
        total = 0.0
        for item in self.bought_basket.items:
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
        for item in self.sold_basket.items:
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
            "status": self.status
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
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        date = datetime.fromisoformat(data.get('date')) if data.get('date') else None
        
        # Parse baskets
        from .basket import Basket
        baskets = {}
        
        if isinstance(data.get('baskets'), dict):
            for name, basket_data in data.get('baskets', {}).items():
                if isinstance(basket_data, dict):
                    basket = Basket.from_dict(basket_data)
                    baskets[name] = basket
        
        # Handle legacy format with separate bought_basket and sold_basket fields
        if data.get('bought_basket') and isinstance(data['bought_basket'], dict):
            bought_basket = Basket.from_dict(data['bought_basket'])
            baskets["bought"] = bought_basket
        
        if data.get('sold_basket') and isinstance(data['sold_basket'], dict):
            sold_basket = Basket.from_dict(data['sold_basket'])
            baskets["sold"] = sold_basket
        
        return cls(
            title=data.get('title', ''),
            content=data.get('content', ''),
            status=data.get('status', 'executed'),
            date=date,
            baskets=baskets,
            id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


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
            source: The source of the fact
            confidence: Confidence level in the fact (0.0 to 1.0)
            date: When the fact was recorded
            baskets: Dictionary of named baskets related to this fact
            **kwargs: Additional arguments passed to the parent class
        """
        super().__init__(title, content, date, baskets, **kwargs)
        self.source = source
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the fact note to a dictionary.
        
        Returns:
            A dictionary representation of the fact note
        """
        data = super().to_dict()
        data.update({
            "source": self.source,
            "confidence": self.confidence
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
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        date = datetime.fromisoformat(data.get('date')) if data.get('date') else None
        
        # Parse baskets
        from .basket import Basket
        baskets = {}
        
        if isinstance(data.get('baskets'), dict):
            for name, basket_data in data.get('baskets', {}).items():
                if isinstance(basket_data, dict):
                    basket = Basket.from_dict(basket_data)
                    baskets[name] = basket
        
        return cls(
            title=data.get('title', ''),
            content=data.get('content', ''),
            source=data.get('source'),
            confidence=data.get('confidence', 1.0),
            date=date,
            baskets=baskets,
            id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


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
        self.time_horizon = time_horizon
        self.risk_level = risk_level
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the strategy note to a dictionary.
        
        Returns:
            A dictionary representation of the strategy note
        """
        data = super().to_dict()
        data.update({
            "time_horizon": self.time_horizon,
            "risk_level": self.risk_level,
            "status": self.status
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
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        date = datetime.fromisoformat(data.get('date')) if data.get('date') else None
        
        # Parse baskets
        from .basket import Basket
        baskets = {}
        
        if isinstance(data.get('baskets'), dict):
            for name, basket_data in data.get('baskets', {}).items():
                if isinstance(basket_data, dict):
                    basket = Basket.from_dict(basket_data)
                    baskets[name] = basket
        
        return cls(
            title=data.get('title', ''),
            content=data.get('content', ''),
            time_horizon=data.get('time_horizon'),
            risk_level=data.get('risk_level'),
            status=data.get('status', 'active'),
            date=date,
            baskets=baskets,
            id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        ) 