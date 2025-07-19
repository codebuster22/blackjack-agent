import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    resetForNextHand, checkShoeExhaustion
)


class TestShoeDepletionReshuffle:
    """Integration test for shoe depletion and reshuffle mid-game."""
    
    def test_shoe_depletion_and_reshuffle(self):
        """
        Test shoe depletion and automatic reshuffle between hands.
        Expected result: Fresh 312-card shoe after reset when below threshold.
        Mock values: GameState with depleted shoe (below threshold).
        Why: Verify automatic reshuffling when shoe is depleted.
        """
        # Initialize game state with a fresh shoe
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        initial_shoe_size = len(state.shoe)
        assert initial_shoe_size == 312
        
        # Place bet and deal first hand
        state = placeBet(state, 20.0)
        state = dealInitialHands(state)
        
        # Verify cards were dealt
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        assert len(state.shoe) == initial_shoe_size - 4
        
        # Manually deplete the shoe to below threshold
        # Remove most cards, leaving only a few
        threshold = 20
        while len(state.shoe) > threshold - 1:
            state.shoe.pop()
        
        # Verify shoe is now below threshold
        assert len(state.shoe) <= threshold - 1
        assert checkShoeExhaustion(state, threshold) is True
        
        # Reset for next hand
        state = resetForNextHand(state)
        
        # Verify fresh shoe was created
        assert len(state.shoe) == 312
        assert checkShoeExhaustion(state, threshold) is False
        
        # Verify hands and bet were cleared
        assert len(state.player_hand.cards) == 0
        assert len(state.dealer_hand.cards) == 0
        assert state.bet == 0.0
        
        # Place bet for second hand
        state = placeBet(state, 25.0)
        assert state.chips == 80.0 - 25.0  # 100 - 20 - 25
        
        # Deal second hand
        state = dealInitialHands(state)
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        assert len(state.shoe) == 312 - 4  # Fresh shoe minus 4 cards
        
        # Verify we can continue playing with the fresh shoe
        assert len(state.shoe) > threshold
    
    def test_multiple_hands_with_reshuffle(self):
        """
        Test multiple hands with automatic reshuffle when needed.
        Expected result: Game continues seamlessly with fresh shoes.
        Mock values: Multiple hands played until shoe depletion.
        Why: Verify continuous gameplay with automatic reshuffling.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe(), chips=200.0)
        threshold = 20
        
        # Play multiple hands
        for hand_num in range(5):
            # Place bet
            bet_amount = 10.0
            state = placeBet(state, bet_amount)
            
            # Deal hands
            state = dealInitialHands(state)
            assert len(state.player_hand.cards) == 2
            assert len(state.dealer_hand.cards) == 2
            
            # Manually deplete shoe if this is hand 2 or 4 (to test reshuffle)
            if hand_num in [1, 3]:
                while len(state.shoe) > threshold - 1:
                    state.shoe.pop()
                assert checkShoeExhaustion(state, threshold) is True
            
            # Reset for next hand
            state = resetForNextHand(state)
            
            # Verify fresh shoe if it was depleted
            if hand_num in [1, 3]:
                assert len(state.shoe) == 312
                assert checkShoeExhaustion(state, threshold) is False
            
            # Verify hands and bet cleared
            assert len(state.player_hand.cards) == 0
            assert len(state.dealer_hand.cards) == 0
            assert state.bet == 0.0
        
        # Verify we can still play after multiple reshuffles
        state = placeBet(state, 15.0)
        state = dealInitialHands(state)
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        assert len(state.shoe) > threshold 