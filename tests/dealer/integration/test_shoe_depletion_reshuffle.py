import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    resetForNextHand, checkShoeExhaustion, set_current_state, get_current_state
)


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
@pytest.mark.asyncio
class TestShoeDepletionReshuffle:
    """Integration test for shoe depletion and reshuffle mid-game."""
    
    async def test_shoe_depletion_and_reshuffle(self, clean_database, mock_tool_context_with_data):
        """
        Test shoe depletion and automatic reshuffle between hands.
        Expected result: Fresh 312-card shoe after reset when below threshold.
        Mock values: GameState with depleted shoe (below threshold).
        Why: Verify automatic reshuffling when shoe is depleted.
        """
        # Initialize game state with a fresh shoe
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        initial_shoe_size = len(state.shoe)
        assert initial_shoe_size == 312
        
        # Place bet and deal first hand
        await placeBet(20.0, mock_tool_context_with_data)
        dealInitialHands()
        current_state = get_current_state()
        
        # Verify cards were dealt
        assert len(current_state.player_hand.cards) == 2
        assert len(current_state.dealer_hand.cards) == 2
        assert len(current_state.shoe) == initial_shoe_size - 4
        
        # Manually deplete the shoe to below threshold
        # Remove most cards, leaving only a few
        threshold = 20
        while len(current_state.shoe) > threshold - 1:
            current_state.shoe.pop()
        
        # Verify shoe is now below threshold
        assert len(current_state.shoe) <= threshold - 1
        shoe_check = checkShoeExhaustion(threshold)
        assert shoe_check["is_exhausted"] is True
        
        # Reset for next hand
        resetForNextHand()
        current_state = get_current_state()
        
        # Verify fresh shoe was created
        assert len(current_state.shoe) == 312
        shoe_check = checkShoeExhaustion(threshold)
        assert shoe_check["is_exhausted"] is False
        
        # Verify hands and bet were cleared
        assert len(current_state.player_hand.cards) == 0
        assert len(current_state.dealer_hand.cards) == 0
        assert current_state.bet == 0.0
        
        # Place bet for second hand
        await placeBet(25.0, mock_tool_context_with_data)
        current_state = get_current_state()
        
        # Deal second hand
        dealInitialHands()
        current_state = get_current_state()
        assert len(current_state.player_hand.cards) == 2
        assert len(current_state.dealer_hand.cards) == 2
        assert len(current_state.shoe) == 312 - 4  # Fresh shoe minus 4 cards
        
        # Verify we can continue playing with the fresh shoe
        assert len(current_state.shoe) > threshold
    
    async def test_multiple_hands_with_reshuffle(self, clean_database, mock_tool_context_with_data):
        """
        Test multiple hands with automatic reshuffle when needed.
        Expected result: Game continues seamlessly with fresh shoes.
        Mock values: Multiple hands played until shoe depletion.
        Why: Verify continuous gameplay with automatic reshuffling.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        threshold = 20
        
        # Play multiple hands
        for hand_num in range(5):
            # Place bet
            bet_amount = 10.0
            await placeBet(bet_amount, mock_tool_context_with_data)
            
            # Deal hands
            dealInitialHands()
            current_state = get_current_state()
            assert len(current_state.player_hand.cards) == 2
            assert len(current_state.dealer_hand.cards) == 2
            
            # Manually deplete shoe if this is hand 2 or 4 (to test reshuffle)
            if hand_num in [1, 3]:
                while len(current_state.shoe) > threshold - 1:
                    current_state.shoe.pop()
                shoe_check = checkShoeExhaustion(threshold)
                assert shoe_check["is_exhausted"] is True
            
            # Reset for next hand
            resetForNextHand()
            current_state = get_current_state()
            
            # Verify fresh shoe if it was depleted
            if hand_num in [1, 3]:
                assert len(current_state.shoe) == 312
                shoe_check = checkShoeExhaustion(threshold)
                assert shoe_check["is_exhausted"] is False
            
            # Verify hands and bet cleared
            assert len(current_state.player_hand.cards) == 0
            assert len(current_state.dealer_hand.cards) == 0
            assert current_state.bet == 0.0
        
        # Verify we can still play after multiple reshuffles
        await placeBet(15.0, mock_tool_context_with_data)
        dealInitialHands()
        current_state = get_current_state()
        assert len(current_state.player_hand.cards) == 2
        assert len(current_state.dealer_hand.cards) == 2
        assert len(current_state.shoe) > threshold 