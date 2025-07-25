import pytest
from unittest.mock import Mock
from dealer_agent.tools.dealer import placeBet, GameState, shuffleShoe, reset_game_state, set_current_state


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
@pytest.mark.asyncio
class TestPlaceBetIntegration:
    """Integration tests for placeBet function with database."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    async def test_normal_bet_deduction(self, clean_database, mock_tool_context_with_data):
        """
        Test normal bet deduction from balance using database.
        Expected result: Balance reduced by bet amount, bet set to amount.
        Mock values: User with balance=100, bet amount=30.
        Why: Verify basic bet placement functionality works correctly with database.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(30.0, mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["balance"] == 70.0  # 100 - 30
        assert result["bet"] == 30.0
    
    async def test_zero_bet_raises_error(self, clean_database, mock_tool_context_with_data):
        """
        Test that zero bet raises error.
        Expected result: Error response with message about positive bet.
        Mock values: User with balance=100, bet amount=0.
        Why: Ensure invalid bet amounts are rejected.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(0.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "positive" in result["error"].lower()
    
    async def test_negative_bet_raises_error(self, clean_database, mock_tool_context_with_data):
        """
        Test that negative bet raises error.
        Expected result: Error response with message about positive bet.
        Mock values: User with balance=100, bet amount=-10.
        Why: Ensure negative bet amounts are rejected.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(-10.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "positive" in result["error"].lower()
    
    async def test_insufficient_balance_raises_error(self, clean_database, mock_tool_context_with_data):
        """
        Test that insufficient balance raises error.
        Expected result: Error response with message about insufficient balance.
        Mock values: User with balance=100, bet amount=150.
        Why: Ensure bets cannot exceed available balance.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(150.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "insufficient" in result["error"].lower()
    
    async def test_exact_balance_bet_succeeds(self, clean_database, mock_tool_context_with_data):
        """
        Test that betting exactly available balance succeeds.
        Expected result: Balance reduced to 0, bet set to amount.
        Mock values: User with balance=100, bet amount=100.
        Why: Verify edge case where bet equals available balance.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(100.0, mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["balance"] == 0.0  # 100 - 100
        assert result["bet"] == 100.0
    
    async def test_bet_must_be_multiple_of_five(self, clean_database, mock_tool_context_with_data):
        """
        Test that bet amount must be a multiple of 5.
        Expected result: Error response with message about multiple of 5.
        Mock values: User with balance=100, bet amount=7.
        Why: Ensure bet amounts follow casino rules.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(7.0, mock_tool_context_with_data)
        
        assert result["success"] is False
        assert "multiple of 5" in result["error"].lower()
    
    async def test_multiple_bets_accumulate_correctly(self, clean_database, mock_tool_context_with_data):
        """
        Test that multiple bets accumulate correctly in game state.
        Expected result: Bet amount increases with each bet placement.
        Mock values: User with balance=100, bet amounts=20, 30.
        Why: Verify bet accumulation works correctly.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        # Place first bet
        result1 = await placeBet(20.0, mock_tool_context_with_data)
        assert result1["success"] is True
        assert result1["bet"] == 20.0
        
        # Place second bet (should accumulate)
        result2 = await placeBet(30.0, mock_tool_context_with_data)
        assert result2["success"] is True
        assert result2["bet"] == 30.0  # New bet amount, not accumulated
    
    async def test_missing_user_id_raises_error(self, clean_database):
        """
        Test that missing user_id raises error.
        Expected result: Error response with message about missing user_id.
        Mock values: Tool context without user_id.
        Why: Ensure proper error handling for missing context.
        """
        # Create tool context without user_id
        tool_context = Mock()
        tool_context.state = {"session_id": "test_session_123"}  # No user_id
        
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = await placeBet(20.0, tool_context)
        
        assert result["success"] is False
        assert "user id not found" in result["error"].lower() 