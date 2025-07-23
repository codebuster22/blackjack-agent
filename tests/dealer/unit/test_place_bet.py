import pytest
from dealer_agent.tools.dealer import placeBet, GameState, shuffleShoe, reset_game_state


class TestPlaceBet:
    """Test the placeBet function."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_normal_bet_deduction(self):
        """
        Test normal bet deduction from chips.
        Expected result: Chips reduced by bet amount, bet set to amount.
        Mock values: GameState with chips=100, bet amount=30.
        Why: Verify basic bet placement functionality works correctly.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        result = placeBet(30.0)
        
        assert result["success"] is True
        assert result["chips"] == 70.0  # 100 - 30
        assert result["bet"] == 30.0
    
    def test_zero_bet_raises_error(self):
        """
        Test that zero bet raises error.
        Expected result: Error response with message about positive bet.
        Mock values: GameState with chips=100, bet amount=0.
        Why: Ensure invalid bet amounts are rejected.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        result = placeBet(0.0)
        
        assert result["success"] is False
        assert "positive" in result["error"].lower()
    
    def test_negative_bet_raises_error(self):
        """
        Test that negative bet raises error.
        Expected result: Error response with message about positive bet.
        Mock values: GameState with chips=100, bet amount=-10.
        Why: Ensure negative bet amounts are rejected.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        result = placeBet(-10.0)
        
        assert result["success"] is False
        assert "positive" in result["error"].lower()
    
    def test_insufficient_chips_raises_error(self):
        """
        Test that insufficient chips raises error.
        Expected result: Error response with message about insufficient chips.
        Mock values: GameState with chips=20, bet amount=50.
        Why: Ensure bets cannot exceed available chips.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(shoe=shuffleShoe(), chips=20.0)
        set_current_state(state)
        
        result = placeBet(50.0)
        
        assert result["success"] is False
        assert "insufficient" in result["error"].lower()
    
    def test_exact_chips_bet_succeeds(self):
        """
        Test that betting exactly available chips succeeds.
        Expected result: Chips reduced to 0, bet set to amount.
        Mock values: GameState with chips=25, bet amount=25.
        Why: Verify edge case where bet equals available chips.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(shoe=shuffleShoe(), chips=25.0)
        set_current_state(state)
        
        result = placeBet(25.0)
        
        assert result["success"] is True
        assert result["chips"] == 0.0  # 25 - 25
        assert result["bet"] == 25.0 