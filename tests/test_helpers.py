"""Tests for utility helper functions."""
import pytest

from src.utils.helpers import get_greeting


def test_get_greeting():
    """Test the get_greeting function."""
    assert get_greeting("World") == "Hello, World!"
    assert get_greeting("Alice") == "Hello, Alice!"
    assert get_greeting("Bob") == "Hello, Bob!"


def test_get_greeting_empty_string():
    """Test get_greeting with empty string."""
    assert get_greeting("") == "Hello, !"


def test_get_greeting_special_characters():
    """Test get_greeting with special characters."""
    assert get_greeting("José") == "Hello, José!"
    assert get_greeting("李明") == "Hello, 李明!"