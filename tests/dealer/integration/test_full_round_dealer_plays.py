import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, processDealerPlay, settleBet, updateChips, displayState, evaluateHand,
    set_current_state, get_current_state
)


class TestFullRoundDealerPlays:
    """Integration test for full round where dealer plays."""
    
    def test_full_round_dealer_plays(self):
        """
        Test complete round where player stands and dealer plays.
        Expected result: Correct result based on final totals.
        Mock values: GameState with chips=100, bet=30.
        Why: Verify complete dealer play flow from bet to settlement.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        # Place bet
        placeBet(30.0)
        current_state = get_current_state()
        assert current_state.chips == 70.0
        assert current_state.bet == 30.0
        
        # Deal initial hands
        dealInitialHands()
        current_state = get_current_state()
        assert len(current_state.player_hand.cards) == 2
        assert len(current_state.dealer_hand.cards) == 2
        
        # Check initial hands
        player_eval = evaluateHand(current_state.player_hand)
        dealer_eval = evaluateHand(current_state.dealer_hand)
        
        # If either has blackjack, this test doesn't apply
        if player_eval.is_blackjack or dealer_eval.is_blackjack:
            pytest.skip("Blackjack detected, dealer play test not applicable")
        
        # Player stands (no action needed, just verify they don't bust)
        if player_eval.is_bust:
            pytest.skip("Player busted on initial deal, dealer play test not applicable")
        
        # Store initial dealer hand size
        initial_dealer_cards = len(current_state.dealer_hand.cards)
        
        # Dealer plays
        processDealerPlay()
        current_state = get_current_state()
        
        # Verify dealer drew cards if needed
        dealer_eval_after = evaluateHand(current_state.dealer_hand)
        if dealer_eval.total < 17:
            # Dealer should have drawn cards
            assert len(current_state.dealer_hand.cards) > initial_dealer_cards
            assert dealer_eval_after.total >= 17
        else:
            # Dealer should not have drawn cards
            assert len(current_state.dealer_hand.cards) == initial_dealer_cards
        
        # Get final hand evaluations before settlement
        final_player_eval = evaluateHand(current_state.player_hand)
        final_dealer_eval = evaluateHand(current_state.dealer_hand)
        
        # Settle the bet
        settle_result = settleBet()
        
        # Verify payout and result are consistent
        if settle_result["result"] == 'win':
            assert settle_result["payout"] == 60.0
        elif settle_result["result"] == 'loss':
            assert settle_result["payout"] == 0.0
        else:  # push
            assert settle_result["payout"] == 30.0
        
        # Update chips with payout (already done in settleBet)
        current_state = get_current_state()
        
        # Verify chips are updated correctly
        expected_chips = 70.0 + settle_result["payout"]
        assert current_state.chips == expected_chips
        
        # Display final state
        display_result = displayState(revealDealerHole=True)
        assert "Player Hand:" in display_result["display_text"]
        assert "Dealer Hand:" in display_result["display_text"]
        assert f"Chips: {current_state.chips}" in display_result["display_text"]
        
        # Verify result matches hand comparison
        if final_player_eval.is_bust:
            assert settle_result["result"] == 'loss'
        elif final_dealer_eval.is_bust:
            assert settle_result["result"] == 'win'
        elif final_player_eval.total > final_dealer_eval.total:
            assert settle_result["result"] == 'win'
        elif final_player_eval.total < final_dealer_eval.total:
            assert settle_result["result"] == 'loss'
        else:
            assert settle_result["result"] == 'push' 