import pytest
from unittest.mock import Mock
from dealer_agent.tools.dealer import placeBet, GameState, shuffleShoe, reset_game_state, set_current_state


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
class TestPlaceBetIntegration:
    """Integration tests for placeBet function with database."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_normal_bet_deduction(self, clean_database, mock_tool_context_with_data):
        """
        Test normal bet deduction from balance using database.
        Expected result: Balance reduced by bet amount, bet set to amount.
        Mock values: User with balance=100, bet amount=30.
        Why: Verify basic bet placement functionality works correctly with database.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(30.0, mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["balance"] == 70.0  # 100 - 30
        assert result["bet"] == 30.0
    
    def test_zero_bet_raises_error(self, clean_database, mock_tool_context_with_data):
        """
        Test that zero bet raises error.
        Expected result: Error response with message about positive bet.
        Mock values: User with balance=100, bet amount=0.
        Why: Ensure invalid bet amounts are rejected.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(0.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "positive" in result["error"].lower()
    
    def test_negative_bet_raises_error(self, clean_database, mock_tool_context_with_data):
        """
        Test that negative bet raises error.
        Expected result: Error response with message about positive bet.
        Mock values: User with balance=100, bet amount=-10.
        Why: Ensure negative bet amounts are rejected.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(-10.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "positive" in result["error"].lower()
    
    def test_insufficient_balance_raises_error(self, clean_database, mock_tool_context_with_data):
        """
        Test that insufficient balance raises error.
        Expected result: Error response with message about insufficient balance.
        Mock values: User with balance=100, bet amount=150.
        Why: Ensure bets cannot exceed available balance.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(150.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "insufficient" in result["error"].lower()
    
    def test_exact_balance_bet_succeeds(self, clean_database, mock_tool_context_with_data):
        """
        Test that betting exactly available balance succeeds.
        Expected result: Balance reduced to 0, bet set to amount.
        Mock values: User with balance=100, bet amount=100.
        Why: Verify edge case where bet equals available balance.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(100.0, mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["balance"] == 0.0  # 100 - 100
        assert result["bet"] == 100.0
    
    def test_bet_must_be_multiple_of_five(self, clean_database, mock_tool_context_with_data):
        """
        Test that bet amount must be a multiple of 5.
        Expected result: Error response with message about multiple of 5.
        Mock values: User with balance=100, bet amount=23.
        Why: Ensure bet validation works correctly.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(23.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "multiple of 5" in result["error"].lower()
    
    def test_multiple_bets_accumulate_correctly(self, clean_database, mock_tool_context_with_data):
        """
        Test that multiple bets accumulate correctly in game state.
        Expected result: Bet amount increases with each call.
        Mock values: User with balance=100, multiple bet amounts.
        Why: Verify bet accumulation works correctly.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        # First bet
        result1 = placeBet(20.0, mock_tool_context_with_data)
        assert result1["success"] is True
        assert result1["bet"] == 20.0
        assert result1["balance"] == 80.0
        
        # Second bet (should replace first bet)
        result2 = placeBet(30.0, mock_tool_context_with_data)
        assert result2["success"] is True
        assert result2["bet"] == 30.0
        assert result2["balance"] == 50.0  # 80 - 30
    
    def test_missing_user_id_raises_error(self, clean_database):
        """
        Test that missing user_id in ToolContext raises error.
        Expected result: Error response with session error.
        Mock values: ToolContext without user_id.
        Why: Ensure proper error handling for missing context.
        """
        # Create mock context without user_id
        mock_context = Mock()
        mock_context.state = {
            "session_id": "test_session_id"
            # Missing user_id
        }
        
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(25.0, mock_context)
        
        assert result["success"] is False
        assert "session error" in result["error"].lower() 