import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, settleBet, updateChips, displayState, evaluateHand
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
        
        # Place bet
        state = placeBet(state, 25.0)
        assert state.chips == 75.0
        assert state.bet == 25.0
        
        # Deal initial hands
        state = dealInitialHands(state)
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        
        # Check initial player hand
        player_eval = evaluateHand(state.player_hand)
        
        # If player already has blackjack, this test doesn't apply
        if player_eval.is_blackjack:
            pytest.skip("Player has blackjack, bust test not applicable")
        
        # Player hits until bust (simulate multiple hits)
        original_shoe_size = len(state.shoe)
        hit_count = 0
        max_hits = 10  # Safety limit to prevent infinite loop
        
        while not player_eval.is_bust and hit_count < max_hits:
            state = processPlayerAction('hit', state)
            hit_count += 1
            player_eval = evaluateHand(state.player_hand)
        
        # Verify player busted or we hit the safety limit
        assert player_eval.is_bust or hit_count >= max_hits
        
        # Verify cards were drawn from shoe
        assert len(state.shoe) < original_shoe_size
        
        # Settle the bet (player should lose due to bust)
        payout, result = settleBet(state)
        
        # Player should lose due to bust
        assert result == 'loss'
        assert payout == -25.0
        
        # Update chips with payout
        state = updateChips(state, payout)
        assert state.chips == 75.0 + payout  # Should be 50.0
        
        # Display final state
        display_result = displayState(state, revealDealerHole=True)
        assert "Player Hand:" in display_result
        assert "Dealer Hand:" in display_result
        assert f"Chips: {state.chips}" in display_result
        
        # Verify player hand total is over 21
        assert player_eval.total > 21 