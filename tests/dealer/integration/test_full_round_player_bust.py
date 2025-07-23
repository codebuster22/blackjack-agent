import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, settleBet, displayState, evaluateHand,
    set_current_state, get_current_state
)


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
class TestFullRoundPlayerBust:
    """Integration test for full round where player hits to bust."""
    
    def test_full_round_player_bust(self, clean_database, mock_tool_context_with_data):
        """
        Test complete round where player hits until bust.
        Expected result: Player loses, no dealer play needed.
        Mock values: GameState with chips=100, bet=25.
        Why: Verify complete bust flow from bet to loss.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        # Place bet
        placeBet(25.0, mock_tool_context_with_data)
        current_state = get_current_state()
        assert current_state.bet == 25.0
        
        # Deal initial hands
        dealInitialHands()
        current_state = get_current_state()
        assert len(current_state.player_hand.cards) == 2
        assert len(current_state.dealer_hand.cards) == 2
        
        # Check initial player hand
        player_eval = evaluateHand(current_state.player_hand)
        
        # If player already has blackjack, this test doesn't apply
        if player_eval.is_blackjack:
            pytest.skip("Player has blackjack, bust test not applicable")
        
        # Player hits until bust (simulate multiple hits)
        original_shoe_size = len(current_state.shoe)
        hit_count = 0
        max_hits = 10  # Safety limit to prevent infinite loop
        
        while not player_eval.is_bust and hit_count < max_hits:
            processPlayerAction('hit')
            current_state = get_current_state()
            hit_count += 1
            player_eval = evaluateHand(current_state.player_hand)
        
        # Verify player busted or we hit the safety limit
        assert player_eval.is_bust or hit_count >= max_hits
        
        # Verify cards were drawn from shoe
        assert len(current_state.shoe) < original_shoe_size
        
        # Settle the bet (player should lose due to bust)
        settle_result = settleBet(mock_tool_context_with_data)
        
        # Player should lose due to bust
        assert settle_result["result"] == 'loss'
        assert settle_result["payout"] == 0.0
        
        # Get current state
        current_state = get_current_state()
        
        # Display final state
        display_result = displayState(revealDealerHole=True, tool_context=mock_tool_context_with_data)
        assert "Player Hand:" in display_result["display_text"]
        assert "Dealer Hand:" in display_result["display_text"]
        assert "Balance:" in display_result["display_text"]
        
        # Verify player hand total is over 21
        assert player_eval.total > 21 