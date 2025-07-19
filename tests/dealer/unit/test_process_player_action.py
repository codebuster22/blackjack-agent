import pytest
from dealer_agent.tools.dealer import processPlayerAction, GameState, Hand, Card, Suit, Rank, shuffleShoe


class TestProcessPlayerAction:
    """Test cases for processPlayerAction() function."""
    
    def test_hit_action(self):
        """
        Test that 'hit' action adds one card to player hand.
        Expected result: Player hand gains one card, shoe size decreases by 1.
        Mock values: State with player hand total < 21.
        Why: Verify hit action correctly draws a card for the player.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ])
        )
        original_shoe_size = len(state.shoe)
        original_hand_size = len(state.player_hand.cards)
        
        state = processPlayerAction('hit', state)
        
        # Check one card added to player hand
        assert len(state.player_hand.cards) == original_hand_size + 1
        # Check shoe size reduced by 1
        assert len(state.shoe) == original_shoe_size - 1
    
    def test_stand_action(self):
        """
        Test that 'stand' action doesn't change player hand or shoe.
        Expected result: No change to player hand or shoe.
        Mock values: State with existing player hand.
        Why: Verify stand action correctly ends player's turn without drawing.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ])
        )
        original_shoe_size = len(state.shoe)
        original_hand_size = len(state.player_hand.cards)
        original_cards = state.player_hand.cards.copy()
        
        state = processPlayerAction('stand', state)
        
        # Check no change to player hand
        assert len(state.player_hand.cards) == original_hand_size
        assert state.player_hand.cards == original_cards
        # Check no change to shoe
        assert len(state.shoe) == original_shoe_size
    
    def test_hit_on_21(self):
        """
        Test that 'hit' action still draws even when player hand total is 21.
        Expected result: Card still drawn despite total being 21.
        Mock values: State with player hand total = 21.
        Why: Verify the function doesn't prevent drawing when total is 21 (logic handled by caller).
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.ace)
            ])
        )
        original_shoe_size = len(state.shoe)
        original_hand_size = len(state.player_hand.cards)
        
        state = processPlayerAction('hit', state)
        
        # Check card still drawn
        assert len(state.player_hand.cards) == original_hand_size + 1
        assert len(state.shoe) == original_shoe_size - 1 