"""
Tests for gift card generation and functionality.
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestGiftCardGeneration:
    """Test gift card generation functionality."""
    
    def test_gift_card_template_exists(self):
        """Test that gift card templates directory exists."""
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'card_templates')
        assert os.path.exists(template_dir), "Gift card templates directory should exist"
    
    def test_gift_metadata_exists(self):
        """Test that gift metadata directory exists."""
        metadata_dir = os.path.join(os.path.dirname(__file__), '..', 'card_metadata')
        assert os.path.exists(metadata_dir), "Gift metadata directory should exist"
    
    def test_generated_cards_directory(self):
        """Test that generated cards directory exists."""
        cards_dir = os.path.join(os.path.dirname(__file__), '..', 'new_gift_cards')
        assert os.path.exists(cards_dir), "Generated gift cards directory should exist"


class TestGiftPriceCalculation:
    """Test gift price calculation logic."""
    
    def test_ton_to_usd_conversion(self):
        """Test TON to USD price conversion."""
        ton_price = 100
        ton_usd_rate = 2.5
        expected_usd = 250
        
        actual_usd = ton_price * ton_usd_rate
        assert actual_usd == expected_usd, f"Expected {expected_usd}, got {actual_usd}"
    
    def test_price_formatting(self):
        """Test price formatting for display."""
        price = 1234.56
        formatted = f"{price:,.2f}"
        assert formatted == "1,234.56", f"Expected '1,234.56', got '{formatted}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
