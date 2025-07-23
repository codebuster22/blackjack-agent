import pytest
from dealer_agent.tools.dealer import checkShoeExhaustion, GameState, shuffleShoe, set_current_state


class TestCheckShoeExhaustion:
    """Test cases for checkShoeExhaustion() function."""
    
    def test_above_threshold(self):
        """
        Test when shoe has more cards than threshold.
        Expected result: False (shoe not exhausted).
        Mock values: Shoe length = threshold + 5, threshold = 20.
        Why: Verify function correctly identifies when shoe has sufficient cards.
        """
        state = GameState(shoe=shuffleShoe()[:25])  # 25 cards, threshold is 20
        set_current_state(state)
        
        result = checkShoeExhaustion(threshold=20)
        
        assert result["success"] is True
        assert result["is_exhausted"] is False
    
    def test_below_threshold(self):
        """
        Test when shoe has fewer cards than threshold.
        Expected result: True (shoe exhausted).
        Mock values: Shoe length = threshold - 1, threshold = 20.
        Why: Verify function correctly identifies when shoe needs reshuffling.
        """
        state = GameState(shoe=shuffleShoe()[:19])  # 19 cards, threshold is 20
        set_current_state(state)
        
        result = checkShoeExhaustion(threshold=20)
        
        assert result["success"] is True
        assert result["is_exhausted"] is True
    
    def test_exactly_at_threshold(self):
        """
        Test when shoe has exactly threshold number of cards.
        Expected result: False (shoe not exhausted).
        Mock values: Shoe length = threshold, threshold = 20.
        Why: Verify boundary condition is handled correctly.
        """
        state = GameState(shoe=shuffleShoe()[:20])  # 20 cards, threshold is 20
        set_current_state(state)
        
        result = checkShoeExhaustion(threshold=20)
        
        assert result["success"] is True
        assert result["is_exhausted"] is False 