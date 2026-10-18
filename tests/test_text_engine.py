import pytest
from PySide6.QtGui import QPainterPath
from core.text_engine import TextEngine

def test_text_to_path_generates_valid_path(qtbot):
    """Test that TextEngine correctly generates a QPainterPath for text."""
    path = TextEngine.text_to_path("Test String", font_family="Arial", font_size=50)
    
    # Assert that a path was returned
    assert isinstance(path, QPainterPath)
    
    # Assert that the path is not empty (it contains some drawing instructions)
    assert not path.isEmpty()
    
def test_arabic_text_support(qtbot):
    """Test that Arabic text is properly shaped and converted."""
    # This specifically tests the bidi/reshaper logic internally
    path = TextEngine.text_to_path("مرحبا", font_family="Arial", font_size=50)
    
    assert isinstance(path, QPainterPath)
    assert not path.isEmpty()
