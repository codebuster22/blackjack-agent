import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, settleBet, updateChips, displayState, evaluateHand,
    set_current_state, get_current_state
)


class TestFullRoundPlayerBust:
    """Integration test for full round where player hits to bust."""
    
    def test_full_round_player_bust(self):
        """
        Test complete round where player hits until bust.
        Expected result: Player loses, no dealer play needed.
        Mock values: GameState with chips=100, bet=25.
        Why: Verify complete bust flow from bet to loss.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        # Place bet
        placeBet(25.0)
        current_state = get_current_state()
        assert current_state.chips == 75.0
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
        settle_result = settleBet()
        
        # Player should lose due to bust
        assert settle_result["result"] == 'loss'
        assert settle_result["payout"] == 0.0
        
        # Update chips with payout (already done in settleBet)
        current_state = get_current_state()
        assert current_state.chips == 75.0 + settle_result["payout"]  # Should be 50.0
        
        # Display final state
        display_result = displayState(revealDealerHole=True)
        assert "Player Hand:" in display_result["display_text"]
        assert "Dealer Hand:" in display_result["display_text"]
        assert f"Chips: {current_state.chips}" in display_result["display_text"]
        
        # Verify player hand total is over 21
        assert player_eval.total > 21 