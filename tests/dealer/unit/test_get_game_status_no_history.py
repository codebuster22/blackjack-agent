import pytest
from dealer_agent.tools.dealer import getGameStatus, initialize_game, placeBet, dealInitialHands, settleBet, resetForNextHand, reset_game_state


class TestGetGameStatusNoHistory:
    """Test that get_game_status() does not include history."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_get_game_status_no_history_in_response(self):
        """Test that get_game_status() does not include history in the response."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Get game status
        status_result = getGameStatus()
        
        assert status_result["success"] is True
        assert "game_state" in status_result
        
        game_state = status_result["game_state"]
        
        # Check that history is NOT included in game_state
        assert "history" not in game_state
        
        # Check that other expected fields are present
        assert "player_hand" in game_state
        assert "dealer_hand" in game_state
        assert "bet" in game_state
        assert "chips" in game_state
        assert "remaining_cards" in game_state
    
    def test_get_game_status_after_rounds_still_no_history(self):
        """Test that get_game_status() still doesn't include history even after playing rounds."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Play a round
        bet_result = placeBet(25.0)
        deal_result = dealInitialHands()
        settle_result = settleBet()
        reset_result = resetForNextHand()
        
        # Get game status
        status_result = getGameStatus()
        
        assert status_result["success"] is True
        game_state = status_result["game_state"]
        
        # Check that history is still NOT included
        assert "history" not in game_state
        
        # Verify that history exists in the actual state but is not exposed
        # This confirms that history is only accessible through get_game_history()
        from dealer_agent.tools.dealer import get_current_state
        actual_state = get_current_state()
        assert len(actual_state.history) >= 1  # History exists
        assert "history" not in game_state  # But not exposed in get_game_status 