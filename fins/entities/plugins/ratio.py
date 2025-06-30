"""
Ratio Plugin - Calculate ratio between two fields from previous pipeline steps
"""
from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Ratio(FieldPlugin):
    """
    Calculates the ratio between two fields from previous pipeline steps.
    
    Useful for creating efficiency metrics, comparisons, and derived indicators.
    Handles division by zero gracefully by returning None.
    
    Args:
        numerator_field: Name of the field to use as numerator
        denominator_field: Name of the field to use as denominator  
        alias: Custom field name (auto-generated if None)
        
    Examples:
        Ratio("RAGR[Med]", "RAGR[Sigma]")           # Med/Sigma efficiency
        Ratio("CAGR", "Vol", alias="risk_adj")      # Risk-adjusted return
        Ratio("MCap", "PE", alias="size_value")     # Size-value composite
    """

    def __init__(self, numerator_field: str, denominator_field: str, alias: str = None):
        # Register call arguments for __str__ representation
        self._register_call_args(numerator_field, denominator_field, alias=alias)
        
        # Generate alias if not provided
        if alias is None:
            alias = f'{numerator_field}/{denominator_field}'
        
        super().__init__(alias=alias)
        
        self.numerator_field = numerator_field
        self.denominator_field = denominator_field

    def field_type(self) -> type:
        return Optional[float]

    def run(self, runtime: 'BasketRuntime'):
        """Override run method to access DataFrame with calculated field values"""
        # Register the ratio field
        runtime.register_field(self.alias, self.field_type())
        
        # Get the current DataFrame with all previously calculated fields
        df = runtime.df()
        
        # Validate that required fields exist
        if self.numerator_field not in df.columns:
            raise RuntimeError(f"Numerator field '{self.numerator_field}' not found. Available fields: {list(df.columns)}")
        if self.denominator_field not in df.columns:
            raise RuntimeError(f"Denominator field '{self.denominator_field}' not found. Available fields: {list(df.columns)}")
        
        # Calculate ratios for each row
        for idx in range(len(df)):
            numerator = df.iloc[idx][self.numerator_field]
            denominator = df.iloc[idx][self.denominator_field]
            
            # Handle None values and division by zero
            if numerator is None or denominator is None or denominator == 0:
                ratio_value = None
            else:
                ratio_value = numerator / denominator
            
            runtime.set_field_value(idx, self.alias, ratio_value)
        
        # Apply any filters if they exist
        if self._filters:
            self._apply_filters(runtime)

    def field_value(self, item: BasketItem):
        """Not used - we override run() method instead"""
        raise NotImplementedError("Ratio plugin uses run() method override") 