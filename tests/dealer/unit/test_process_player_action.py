import pytest
from dealer_agent.tools.dealer import processPlayerAction, GameState, shuffleShoe, Card, Suit, Rank, Hand, reset_game_state


class TestProcessPlayerAction:
    """Test the processPlayerAction function."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_hit_action(self):
        """
        Test that 'hit' action adds one card to player hand.
        Expected result: Player hand gains one card, shoe size decreases by 1.
        Mock values: State with player hand total < 21.
        Why: Verify hit action correctly draws a card for the player.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ])
        )
        set_current_state(state)
        
        result = processPlayerAction('hit')
        
        assert result["success"] is True
        assert len(result["player_hand"]["cards"]) == 3  # 2 original + 1 hit
        assert result["remaining_cards"] == 311  # 312 - 1 card drawn
    
    def test_stand_action(self):
        """
        Test that 'stand' action doesn't change player hand or shoe.
        Expected result: No change to player hand or shoe.
        Mock values: State with existing player hand.
        Why: Verify stand action correctly ends player's turn without drawing.
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ])
        )
        set_current_state(state)
        
        result = processPlayerAction('stand')
        
        assert result["success"] is True
        assert len(result["player_hand"]["cards"]) == 2  # No change
        assert result["remaining_cards"] == 312  # No change to shoe
    
    def test_hit_on_21(self):
        """
        Test that 'hit' action still draws even when player hand total is 21.
        Expected result: Card still drawn despite total being 21.
        Mock values: State with player hand total = 21.
        Why: Verify the function doesn't prevent drawing when total is 21 (logic handled by caller).
        """
        # Initialize game state
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.ace)
            ])
        )
        set_current_state(state)
        
        result = processPlayerAction('hit')
        
        assert result["success"] is True
        assert len(result["player_hand"]["cards"]) == 3  # 2 original + 1 hit
        assert result["remaining_cards"] == 311  # 312 - 1 card drawn 