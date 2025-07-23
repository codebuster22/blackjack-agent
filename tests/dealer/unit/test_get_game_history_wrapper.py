import pytest
from dealer_agent.tools.dealer import getGameHistory, initialize_game, placeBet, dealInitialHands, settleBet, resetForNextHand, reset_game_state


class TestGetGameHistory:
    """Test the get_game_history function."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_get_game_history_empty(self):
        """Test getting history when no rounds have been played."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Get history
        result = getGameHistory()
        
        assert result["success"] is True
        assert result["total_rounds"] == 0
        assert len(result["history"]) == 0
        assert "statistics" in result
        assert result["statistics"]["total_rounds"] == 0
        assert result["statistics"]["wins"] == 0
        assert result["statistics"]["losses"] == 0
        assert result["statistics"]["pushes"] == 0
        assert result["statistics"]["win_rate"] == 0.0
    
    def test_get_game_history_after_rounds(self):
        """Test getting history after playing some rounds."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Play a round
        bet_result = placeBet(25.0)
        assert bet_result["success"] is True
        
        deal_result = dealInitialHands()
        assert deal_result["success"] is True
        
        settle_result = settleBet()
        assert settle_result["success"] is True
        
        reset_result = resetForNextHand()
        assert reset_result["success"] is True
        
        # Get history
        history_result = getGameHistory()
        
        assert history_result["success"] is True
        assert history_result["total_rounds"] == 1
        assert len(history_result["history"]) == 1
        
        # Check round data
        round_data = history_result["history"][0]
        assert round_data["round_number"] == 1
        assert round_data["bet_amount"] == 25.0
        assert len(round_data["player_hand"]) == 2
        assert len(round_data["dealer_hand"]) == 2
        
        # Check statistics
        stats = history_result["statistics"]
        assert stats["total_rounds"] == 1
        assert stats["total_bet"] == 25.0
        assert stats["wins"] + stats["losses"] + stats["pushes"] == 1
    
    def test_get_game_history_multiple_rounds(self):
        """Test getting history after multiple rounds."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Play multiple rounds
        for i in range(3):
            bet_result = placeBet(20.0)
            assert bet_result["success"] is True
            
            deal_result = dealInitialHands()
            assert deal_result["success"] is True
            
            settle_result = settleBet()
            assert settle_result["success"] is True
            
            reset_result = resetForNextHand()
            assert reset_result["success"] is True
        
        # Get history
        history_result = getGameHistory()
        
        assert history_result["success"] is True
        assert history_result["total_rounds"] == 3
        assert len(history_result["history"]) == 3
        
        # Check all rounds
        for i, round_data in enumerate(history_result["history"]):
            assert round_data["round_number"] == i + 1
            assert round_data["bet_amount"] == 20.0
        
        # Check statistics
        stats = history_result["statistics"]
        assert stats["total_rounds"] == 3
        assert stats["total_bet"] == 60.0  # 3 * 20
        assert stats["wins"] + stats["losses"] + stats["pushes"] == 3
    
    def test_get_game_history_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Play a round (we can't control the outcome, but we can test the structure)
        bet_result = placeBet(25.0)
        deal_result = dealInitialHands()
        settle_result = settleBet()
        reset_result = resetForNextHand()
        
        # Get history
        history_result = getGameHistory()
        
        stats = history_result["statistics"]
        
        # Check that all required fields are present
        assert "total_rounds" in stats
        assert "wins" in stats
        assert "losses" in stats
        assert "pushes" in stats
        assert "win_rate" in stats
        assert "total_bet" in stats
        assert "net_profit" in stats
        
        # Check that values are reasonable
        assert stats["total_rounds"] == 1
        assert stats["wins"] >= 0
        assert stats["losses"] >= 0
        assert stats["pushes"] >= 0
        assert 0.0 <= stats["win_rate"] <= 1.0
        assert stats["total_bet"] == 25.0
        assert isinstance(stats["net_profit"], float) 