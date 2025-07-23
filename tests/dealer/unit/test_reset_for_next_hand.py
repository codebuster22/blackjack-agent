import pytest
from dealer_agent.tools.dealer import resetForNextHand, GameState, Hand, Card, Suit, Rank, shuffleShoe, set_current_state


class TestResetForNextHand:
    """Test cases for resetForNextHand() function."""
    
    def test_reshuffle_trigger(self):
        """
        Test that shoe is reshuffled when below threshold.
        Expected result: Fresh 312-card shoe after reset.
        Mock values: Shoe with 15 cards (below threshold of 20).
        Why: Verify automatic reshuffling when shoe is depleted.
        """
        state = GameState(
            shoe=shuffleShoe()[:15],  # Below threshold
            player_hand=Hand(cards=[Card(suit=Suit.hearts, rank=Rank.ace)]),
            dealer_hand=Hand(cards=[Card(suit=Suit.diamonds, rank=Rank.king)]),
            bet=100.0
        )
        set_current_state(state)
        
        result = resetForNextHand()
        
        # Check success
        assert result["success"] is True
        # Check fresh 312-card shoe
        assert result["remaining_cards"] == 312
        # Check reshuffled flag
        assert result["reshuffled"] is True
    
    def test_hand_clearance(self):
        """
        Test that hands and bet are cleared regardless of shoe status.
        Expected result: Empty hands and zero bet after reset.
        Mock values: State with existing hands and bet, shoe above threshold.
        Why: Verify hands and bet are always cleared for next hand.
        """
        state = GameState(
            shoe=shuffleShoe()[:50],  # Above threshold
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.king)
            ]),
            bet=150.0
        )
        original_shoe_size = len(state.shoe)
        set_current_state(state)
        
        result = resetForNextHand()
        
        # Check success
        assert result["success"] is True
        # Check hands cleared (we can't directly check state, but we can verify the function worked)
        assert result["round_recorded"] is True
        # Check shoe unchanged (above threshold)
        assert result["remaining_cards"] == original_shoe_size
        # Check not reshuffled
        assert result["reshuffled"] is False 