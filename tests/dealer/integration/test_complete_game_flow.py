import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, processDealerPlay, settleBet, updateChips, 
    resetForNextHand, displayState, evaluateHand, set_current_state, get_current_state
)


class TestCompleteGameFlow:
    """Comprehensive integration test for complete game flow."""
    
    def test_complete_game_session(self):
        """
        Test a complete game session with multiple hands and different outcomes.
        Expected result: Game handles various scenarios correctly.
        Mock values: Multiple hands with different strategies and outcomes.
        Why: Verify the complete blackjack game flow works end-to-end.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe(), chips=200.0)
        set_current_state(state)
        initial_chips = state.chips
        
        # Track game statistics
        wins = 0
        losses = 0
        pushes = 0
        
        # Play multiple hands
        for hand_num in range(3):
            # Place bet
            bet_amount = 20.0
            placeBet(bet_amount)
            
            # Deal initial hands
            dealInitialHands()
            current_state = get_current_state()
            assert len(current_state.player_hand.cards) == 2
            assert len(current_state.dealer_hand.cards) == 2
            
            # Evaluate initial hands
            player_eval = evaluateHand(current_state.player_hand)
            dealer_eval = evaluateHand(current_state.dealer_hand)
            
            # Handle different scenarios
            if player_eval.is_blackjack:
                # Player blackjack - no further action needed
                pass
            elif dealer_eval.is_blackjack:
                # Dealer blackjack - no further action needed
                pass
            elif player_eval.is_bust:
                # Player busted on initial deal
                pass
            else:
                # Normal play - player can hit or stand
                # For this test, we'll simulate different strategies
                if hand_num == 0:
                    # First hand: Hit until 17 or bust
                    while player_eval.total < 17 and not player_eval.is_bust:
                        processPlayerAction('hit')
                        current_state = get_current_state()
                        player_eval = evaluateHand(current_state.player_hand)
                elif hand_num == 1:
                    # Second hand: Stand immediately
                    pass  # No action needed
                else:
                    # Third hand: Hit once then stand
                    if player_eval.total < 21:
                        processPlayerAction('hit')
                        current_state = get_current_state()
                        player_eval = evaluateHand(current_state.player_hand)
                
                # Dealer plays if player didn't bust
                if not player_eval.is_bust:
                    processDealerPlay()
            
            # Settle the bet
            settle_result = settleBet()
            
            # Update statistics
            if settle_result["result"] == 'win':
                wins += 1
            elif settle_result["result"] == 'loss':
                losses += 1
            else:
                pushes += 1
            
            # Update chips (already done in settleBet)
            current_state = get_current_state()
            
            # Verify payout consistency
            if settle_result["result"] == 'win':
                # Check if it's a blackjack (1.5x payout) or regular win (1x payout)
                # We need to check the player evaluation before settlement
                if player_eval.is_blackjack:
                    assert settle_result["payout"] == bet_amount * 2.5  # bet back + 1.5x winnings
                else:
                    assert settle_result["payout"] == bet_amount * 2  # bet back + equal winnings
            elif settle_result["result"] == 'loss':
                assert settle_result["payout"] == 0.0
            else:  # push
                assert settle_result["payout"] == bet_amount
            
            # Display state for this hand
            display_result = displayState(revealDealerHole=True)
            assert "Player Hand:" in display_result["display_text"]
            assert "Dealer Hand:" in display_result["display_text"]
            assert f"Chips: {current_state.chips}" in display_result["display_text"]
            
            # Reset for next hand (unless this is the last hand)
            if hand_num < 2:
                resetForNextHand()
                current_state = get_current_state()
                assert len(current_state.player_hand.cards) == 0
                assert len(current_state.dealer_hand.cards) == 0
                assert current_state.bet == 0.0
        
        # Verify final statistics
        assert wins + losses + pushes == 3
        
        # Verify chips changed (unless all were pushes)
        if pushes < 3:
            current_state = get_current_state()
            assert current_state.chips != initial_chips
        
        # Verify we can continue playing
        current_state = get_current_state()
        assert len(current_state.shoe) > 0
    
    def test_edge_case_continuous_play(self):
        """
        Test edge case of continuous play with various hand outcomes.
        Expected result: Game handles edge cases gracefully.
        Mock values: Multiple hands with edge case scenarios.
        Why: Verify game robustness with unusual scenarios.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        # Play hands until we run out of chips or cards
        hand_count = 0
        max_hands = 10  # Safety limit
        
        while get_current_state().chips >= 5.0 and hand_count < max_hands:
            # Place minimum bet
            bet_amount = 5.0
            placeBet(bet_amount)
            
            # Deal hands
            dealInitialHands()
            
            # Quick settlement (no player/dealer action for speed)
            settleBet()
            
            # Reset for next hand
            resetForNextHand()
            
            hand_count += 1
        
        # Verify we played some hands
        assert hand_count > 0
        
        # Verify final state is valid
        current_state = get_current_state()
        assert len(current_state.player_hand.cards) == 0
        assert len(current_state.dealer_hand.cards) == 0
        assert current_state.bet == 0.0
        assert current_state.chips >= 0.0  # Shouldn't go negative 