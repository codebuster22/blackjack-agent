import pytest
from dealer_agent.tools.dealer import processDealerPlay, GameState, Hand, Card, Suit, Rank, shuffleShoe, evaluateHand


class TestProcessDealerPlay:
    """Test cases for processDealerPlay() function."""
    
    def test_dealer_hits_up_to_17(self):
        """
        Test that dealer draws cards until total >= 17.
        Expected result: Dealer draws cards until total reaches or exceeds 17.
        Mock values: Dealer hand with total 12.
        Why: Verify dealer follows standard blackjack rules of hitting on 16 and below.
        """
        state = GameState(
            shoe=shuffleShoe(),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.two)
            ])
        )
        original_shoe_size = len(state.shoe)
        
        state = processDealerPlay(state)
        
        # Check dealer hand total is >= 17
        dealer_eval = evaluateHand(state.dealer_hand)
        assert dealer_eval.total >= 17
        # Check cards were drawn from shoe
        assert len(state.shoe) < original_shoe_size
    
    def test_soft_17_stand(self):
        """
        Test that dealer stands on soft 17 (A+6).
        Expected result: No additional cards drawn when dealer has soft 17.
        Mock values: Dealer hand with [A, 6] (soft 17).
        Why: Verify dealer follows soft 17 rule correctly.
        """
        state = GameState(
            shoe=shuffleShoe(),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.diamonds, rank=Rank.six)
            ])
        )
        original_shoe_size = len(state.shoe)
        original_hand_size = len(state.dealer_hand.cards)
        
        state = processDealerPlay(state)
        
        # Check no additional cards drawn
        assert len(state.dealer_hand.cards) == original_hand_size
        assert len(state.shoe) == original_shoe_size
        # Verify total is 17
        dealer_eval = evaluateHand(state.dealer_hand)
        assert dealer_eval.total == 17
        assert dealer_eval.is_soft is True
    
    def test_immediate_stand_on_17_plus(self):
        """
        Test that dealer stands immediately when total >= 17.
        Expected result: No cards drawn when dealer already has 17 or higher.
        Mock values: Dealer hand with [10, 7] (total 17).
        Why: Verify dealer doesn't draw unnecessarily when already at or above 17.
        """
        state = GameState(
            shoe=shuffleShoe(),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.seven)
            ])
        )
        original_shoe_size = len(state.shoe)
        original_hand_size = len(state.dealer_hand.cards)
        
        state = processDealerPlay(state)
        
        # Check no additional cards drawn
        assert len(state.dealer_hand.cards) == original_hand_size
        assert len(state.shoe) == original_shoe_size
        # Verify total is 17
        dealer_eval = evaluateHand(state.dealer_hand)
        assert dealer_eval.total == 17 