"""
Tests for the FlowCommand base class.
"""

import pytest
from typing import Type
from ..storage.entity import Entity
from ..dsl.flow_command import FlowCommand

# Test entities
class TestInputEntity(Entity):
    """Test input entity type."""
    def __init__(self, value):
        self.value = value
        
    def to_dict(self):
        return {"value": self.value}

class TestOutputEntity(Entity):
    """Test output entity type."""
    def __init__(self, value):
        self.value = value
        
    def to_dict(self):
        return {"value": self.value}

# Test command implementation
class TestCommand(FlowCommand):
    """Test command that doubles its input value."""
    
    @property
    def input_type(self) -> Type[Entity]:
        return TestInputEntity
        
    @property
    def output_type(self) -> Type[Entity]:
        return TestOutputEntity
        
    @property
    def description(self) -> str:
        return "Test command that doubles its input value"
        
    @property
    def parameters(self) -> dict:
        return {
            "multiplier": "Value to multiply by (default: 2)"
        }
        
    @property
    def examples(self) -> dict:
        return {
            "input -> double": "Doubles the input value",
            "input -> double multiplier=3": "Triples the input value"
        }
        
    def execute(self, input_entity: Entity) -> Entity:
        self.validate_input(input_entity)
        multiplier = self.params.get("multiplier", 2)
        return TestOutputEntity(input_entity.value * multiplier)

def test_command_initialization():
    """Test command initialization with parameters."""
    cmd = TestCommand(multiplier=3)
    assert cmd.params["multiplier"] == 3

def test_input_validation_success():
    """Test input validation with correct type."""
    cmd = TestCommand()
    input_entity = TestInputEntity(5)
    cmd.validate_input(input_entity)  # Should not raise

def test_input_validation_failure():
    """Test input validation with incorrect type."""
    cmd = TestCommand()
    wrong_input = TestOutputEntity(5)  # Wrong type
    with pytest.raises(TypeError):
        cmd.validate_input(wrong_input)

def test_command_execution():
    """Test command execution with valid input."""
    cmd = TestCommand(multiplier=3)
    input_entity = TestInputEntity(5)
    result = cmd.execute(input_entity)
    
    assert isinstance(result, TestOutputEntity)
    assert result.value == 15

def test_command_execution_with_wrong_input():
    """Test command execution with invalid input type."""
    cmd = TestCommand()
    wrong_input = TestOutputEntity(5)  # Wrong type
    with pytest.raises(TypeError):
        cmd.execute(wrong_input)

def test_help_text_generation():
    """Test help text generation."""
    cmd = TestCommand()
    help_text = cmd.help()
    
    # Check that help text contains all required sections
    assert "Command: TestCommand" in help_text
    assert "Test command that doubles its input value" in help_text
    assert "Input: TestInputEntity" in help_text
    assert "Output: TestOutputEntity" in help_text
    assert "Parameters:" in help_text
    assert "multiplier:" in help_text
    assert "Examples:" in help_text
    assert "input -> double" in help_text 