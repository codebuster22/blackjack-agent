import pytest
from dealer_agent.tools.dealer import initialize_game, reset_game_state, drawCard


class TestDrawCard:
    """Test the drawCard function."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_draw_card_success(self):
        """Test successful card drawing."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Draw a card
        result = drawCard()
        
        assert result["success"] is True
        assert "drawn_card" in result
        assert "suit" in result["drawn_card"]
        assert "rank" in result["drawn_card"]
        assert "player_hand" in result
        assert len(result["player_hand"]["cards"]) == 1
        assert result["remaining_cards"] == 311  # 312 - 1 card drawn
    
    def test_draw_card_empty_shoe(self):
        """Test drawing from empty shoe."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Draw all cards from shoe (312 cards)
        for _ in range(312):
            result = drawCard()
            assert result["success"] is True
        
        # Try to draw one more card
        result = drawCard()
        assert result["success"] is False
        assert "Shoe is empty" in result["error"]
    
    def test_draw_card_multiple_cards(self):
        """Test drawing multiple cards."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Draw multiple cards
        for i in range(5):
            result = drawCard()
            assert result["success"] is True
            assert len(result["player_hand"]["cards"]) == i + 1
            assert result["remaining_cards"] == 312 - (i + 1)
    
    def test_draw_card_hand_evaluation(self):
        """Test that hand evaluation is updated after drawing."""
        # Initialize game
        init_result = initialize_game()
        assert init_result["success"] is True
        
        # Draw a card
        result = drawCard()
        assert result["success"] is True
        
        # Check that hand evaluation is included
        assert "player_bust" in result
        assert "player_blackjack" in result
        assert isinstance(result["player_bust"], bool)
        assert isinstance(result["player_blackjack"], bool) 