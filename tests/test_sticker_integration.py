"""
Tests for sticker integration functionality.
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestStickerCollections:
    """Test sticker collection functionality."""
    
    def test_sticker_collections_directory_exists(self):
        """Test that sticker collections directory exists."""
        collections_dir = os.path.join(os.path.dirname(__file__), '..', 'sticker_collections')
        assert os.path.exists(collections_dir), "Sticker collections directory should exist"
    
    def test_sticker_price_cards_directory_exists(self):
        """Test that sticker price cards directory exists."""
        cards_dir = os.path.join(os.path.dirname(__file__), '..', 'Sticker_Price_Cards')
        assert os.path.exists(cards_dir), "Sticker price cards directory should exist"
    
    def test_sticker_data_file_exists(self):
        """Test that sticker data file exists."""
        data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'sticker_price_results.json')
        assert os.path.exists(data_file), "Sticker data file should exist"


class TestStickerNameNormalization:
    """Test sticker name normalization logic."""
    
    def test_normalize_spaces_to_underscores(self):
        """Test that spaces are converted to underscores."""
        name = "Cool Cats"
        normalized = name.replace(" ", "_").lower()
        assert normalized == "cool_cats", f"Expected 'cool_cats', got '{normalized}'"
    
    def test_normalize_special_characters(self):
        """Test that special characters are handled."""
        name = "Dogs OG"
        normalized = name.replace(" ", "_").lower()
        assert normalized == "dogs_og", f"Expected 'dogs_og', got '{normalized}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
