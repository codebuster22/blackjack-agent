import pytest
from dealer_agent.tools.dealer import (
    GameState, shuffleShoe, placeBet, dealInitialHands, 
    processPlayerAction, processDealerPlay, settleBet, displayState, evaluateHand,
    set_current_state, get_current_state
)


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
@pytest.mark.asyncio
class TestFullRoundDealerPlays:
    """Integration test for full round where dealer plays."""
    
    async def test_full_round_dealer_plays(self, clean_database, mock_tool_context_with_data):
        """
        Test complete round where player stands and dealer plays.
        Expected result: Correct result based on final totals.
        Mock values: GameState with chips=100, bet=30.
        Why: Verify complete dealer play flow from bet to settlement.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        # Place bet
        await placeBet(30.0, mock_tool_context_with_data)
        current_state = get_current_state()
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
        
        # Player explicitly stands
        processPlayerAction('stand')
        current_state = get_current_state()
        
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
        settle_result = await settleBet(mock_tool_context_with_data)
        
        # Verify payout and result are consistent
        if settle_result["result"] == 'win':
            assert settle_result["payout"] == 60.0
        elif settle_result["result"] == 'loss':
            assert settle_result["payout"] == 0.0
        else:  # push
            assert settle_result["payout"] == 30.0
        
        # Get current state
        current_state = get_current_state()
        
        # Display final state
        display_result = await displayState(revealDealerHole=True, tool_context=mock_tool_context_with_data)
        assert "Player Hand:" in display_result["display_text"]
        assert "Dealer Hand:" in display_result["display_text"]
        assert "Balance:" in display_result["display_text"]
        
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