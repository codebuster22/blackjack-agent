import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, processDealerPlay, settleBet, updateChips, 
    resetForNextHand, displayState, evaluateHand
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
        initial_chips = state.chips
        
        # Track game statistics
        wins = 0
        losses = 0
        pushes = 0
        
        # Play multiple hands
        for hand_num in range(3):
            # Place bet
            bet_amount = 20.0
            state = placeBet(state, bet_amount)
            
            # Deal initial hands
            state = dealInitialHands(state)
            assert len(state.player_hand.cards) == 2
            assert len(state.dealer_hand.cards) == 2
            
            # Evaluate initial hands
            player_eval = evaluateHand(state.player_hand)
            dealer_eval = evaluateHand(state.dealer_hand)
            
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
                        state = processPlayerAction('hit', state)
                        player_eval = evaluateHand(state.player_hand)
                elif hand_num == 1:
                    # Second hand: Stand immediately
                    pass  # No action needed
                else:
                    # Third hand: Hit once then stand
                    if player_eval.total < 21:
                        state = processPlayerAction('hit', state)
                        player_eval = evaluateHand(state.player_hand)
                
                # Dealer plays if player didn't bust
                if not player_eval.is_bust:
                    state = processDealerPlay(state)
            
            # Settle the bet
            payout, result = settleBet(state)
            
            # Update statistics
            if result == 'win':
                wins += 1
            elif result == 'loss':
                losses += 1
            else:
                pushes += 1
            
            # Update chips
            state = updateChips(state, payout)
            
            # Verify payout consistency
            if result == 'win':
                # Check if it's a blackjack (1.5x payout) or regular win (1x payout)
                player_eval = evaluateHand(state.player_hand)
                if player_eval.is_blackjack:
                    assert payout == bet_amount * 1.5
                else:
                    assert payout == bet_amount
            elif result == 'loss':
                assert payout == -bet_amount
            else:  # push
                assert payout == 0.0
            
            # Display state for this hand
            display_result = displayState(state, revealDealerHole=True)
            assert "Player Hand:" in display_result
            assert "Dealer Hand:" in display_result
            assert f"Chips: {state.chips}" in display_result
            
            # Reset for next hand (unless this is the last hand)
            if hand_num < 2:
                state = resetForNextHand(state)
                assert len(state.player_hand.cards) == 0
                assert len(state.dealer_hand.cards) == 0
                assert state.bet == 0.0
        
        # Verify final statistics
        assert wins + losses + pushes == 3
        
        # Verify chips changed (unless all were pushes)
        if pushes < 3:
            assert state.chips != initial_chips
        
        # Verify we can continue playing
        assert len(state.shoe) > 0
    
    def test_edge_case_continuous_play(self):
        """
        Test edge case of continuous play with various hand outcomes.
        Expected result: Game handles edge cases gracefully.
        Mock values: Multiple hands with edge case scenarios.
        Why: Verify game robustness with unusual scenarios.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        
        # Play hands until we run out of chips or cards
        hand_count = 0
        max_hands = 10  # Safety limit
        
        while state.chips >= 5.0 and hand_count < max_hands:
            # Place minimum bet
            bet_amount = 5.0
            state = placeBet(state, bet_amount)
            
            # Deal hands
            state = dealInitialHands(state)
            
            # Quick settlement (no player/dealer action for speed)
            payout, result = settleBet(state)
            state = updateChips(state, payout)
            
            # Reset for next hand
            state = resetForNextHand(state)
            
            hand_count += 1
        
        # Verify we played some hands
        assert hand_count > 0
        
        # Verify final state is valid
        assert len(state.player_hand.cards) == 0
        assert len(state.dealer_hand.cards) == 0
        assert state.bet == 0.0
        assert state.chips >= 0.0  # Shouldn't go negative 