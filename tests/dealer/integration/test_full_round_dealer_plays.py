import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, processDealerPlay, settleBet, updateChips, displayState, evaluateHand
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
        
        # Place bet
        state = placeBet(state, 30.0)
        assert state.chips == 70.0
        assert state.bet == 30.0
        
        # Deal initial hands
        state = dealInitialHands(state)
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        
        # Check initial hands
        player_eval = evaluateHand(state.player_hand)
        dealer_eval = evaluateHand(state.dealer_hand)
        
        # If either has blackjack, this test doesn't apply
        if player_eval.is_blackjack or dealer_eval.is_blackjack:
            pytest.skip("Blackjack detected, dealer play test not applicable")
        
        # Player stands (no action needed, just verify they don't bust)
        if player_eval.is_bust:
            pytest.skip("Player busted on initial deal, dealer play test not applicable")
        
        # Store initial dealer hand size
        initial_dealer_cards = len(state.dealer_hand.cards)
        
        # Dealer plays
        state = processDealerPlay(state)
        
        # Verify dealer drew cards if needed
        dealer_eval_after = evaluateHand(state.dealer_hand)
        if dealer_eval.total < 17:
            # Dealer should have drawn cards
            assert len(state.dealer_hand.cards) > initial_dealer_cards
            assert dealer_eval_after.total >= 17
        else:
            # Dealer should not have drawn cards
            assert len(state.dealer_hand.cards) == initial_dealer_cards
        
        # Settle the bet
        payout, result = settleBet(state)
        
        # Verify payout and result are consistent
        if result == 'win':
            assert payout == 30.0
        elif result == 'loss':
            assert payout == -30.0
        else:  # push
            assert payout == 0.0
        
        # Update chips with payout
        state = updateChips(state, payout)
        
        # Verify chips are updated correctly
        expected_chips = 70.0 + payout
        assert state.chips == expected_chips
        
        # Display final state
        display_result = displayState(state, revealDealerHole=True)
        assert "Player Hand:" in display_result
        assert "Dealer Hand:" in display_result
        assert f"Chips: {state.chips}" in display_result
        
        # Verify final hand evaluations
        final_player_eval = evaluateHand(state.player_hand)
        final_dealer_eval = evaluateHand(state.dealer_hand)
        
        # Verify result matches hand comparison
        if final_player_eval.is_bust:
            assert result == 'loss'
        elif final_dealer_eval.is_bust:
            assert result == 'win'
        elif final_player_eval.total > final_dealer_eval.total:
            assert result == 'win'
        elif final_player_eval.total < final_dealer_eval.total:
            assert result == 'loss'
        else:
            assert result == 'push' 