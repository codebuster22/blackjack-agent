import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dealer_agent.tools.dealer import (
    placeBetAndDealInitialHands,
    processPlayerAction,
    processDealerPlay,
    settleBet,
    displayState,
    GameState,
    shuffleShoe,
    Card,
    Suit,
    Rank,
    Hand,
    reset_game_state,
    get_current_state,
    set_current_state,
    _validate_game_state_consistency
)
from google.adk.tools.tool_context import ToolContext


class TestStateCorruptionPrevention:
    """Integration tests to verify that validation prevents the original state corruption bug."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    @pytest.mark.asyncio
    async def test_original_bug_scenario_prevented(self):
        """
        Test that the original bug scenario (state corruption during hit) is prevented.
        Expected result: Validation catches the corruption and prevents invalid actions.
        Mock values: Simulate the exact scenario from the original gameplay log.
        Why: Verify that our validation fixes prevent the original bug.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock user manager for successful bet placement
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1010.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Step 1: Initialize game and place bet atomically (this prevents the original issue)
            result = await placeBetAndDealInitialHands(500.0, tool_context)
            
            assert result["success"] is True
            assert result["bet"] == 500.0
            assert len(result["player_hand"]["cards"]) == 2
            
            # Verify game state is valid after atomic operation
            state = get_current_state()
            is_valid, error_msg = _validate_game_state_consistency(state)
            assert is_valid is True, f"State corruption detected: {error_msg}"
            
            # Step 2: Player hits - this should work correctly now
            hit_result = processPlayerAction('hit')
            
            # Should succeed (unlike in original bug)
            assert hit_result["success"] is True
            assert len(hit_result["player_hand"]["cards"]) == 3  # 2 initial + 1 hit
            
            # Verify state is still consistent after hit
            state = get_current_state()
            is_valid, error_msg = _validate_game_state_consistency(state)
            assert is_valid is True, f"State corruption after hit: {error_msg}"
            
            # Step 3: Display state should show consistent information
            display_result = await displayState(tool_context=tool_context)
            
            assert display_result["success"] is True
            assert len(display_result["player_hand"]["cards"]) == 3
            # Should not show inconsistent data like "only 4♥" from original bug
            
    def test_validation_prevents_action_without_proper_setup(self):
        """
        Test that validation prevents actions when proper setup hasn't occurred.
        Expected result: Clear error messages for each invalid action attempt.
        Mock values: Various incomplete game states.
        Why: Verify validation catches the root cause of the original bug.
        """
        # Try to hit without any setup
        result = processPlayerAction('hit')
        assert result["success"] is False
        assert "initial hands have not been dealt" in result["error"].lower()
        
        # Try to hit with hands but no bet
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=0.0
        )
        set_current_state(state)
        
        result = processPlayerAction('hit')
        assert result["success"] is False
        assert "no bet has been placed" in result["error"].lower()
        
        # Try dealer play when player has initial hands (now allowed - implicit stand)
        state.bet = 100.0
        set_current_state(state)

        result = processDealerPlay()
        # This should now succeed because we allow dealer to play when player implicitly stands
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_complete_game_flow_with_validation(self):
        """
        Test a complete game flow to ensure validation doesn't break normal gameplay.
        Expected result: All operations succeed in proper sequence.
        Mock values: Normal gameplay scenario.
        Why: Verify validation allows valid operations while preventing invalid ones.
        """
        # Mock tool context and services
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1000.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_user_manager.credit_user_balance.return_value = True
            
            mock_db_service = AsyncMock()
            mock_db_service.save_round.return_value = True
            mock_db_service.update_session_status.return_value = True
            
            mock_service_manager.user_manager = mock_user_manager
            mock_service_manager.db_service = mock_db_service
            
            # Step 1: Atomic bet and deal
            result = await placeBetAndDealInitialHands(100.0, tool_context)
            assert result["success"] is True
            
            # Step 2: Player stands (to avoid dealing with random hit outcomes)
            result = processPlayerAction('stand')
            assert result["success"] is True
            
            # Step 3: Dealer plays
            result = processDealerPlay()
            assert result["success"] is True
            
            # Step 4: Settle bet
            result = await settleBet(tool_context)
            assert result["success"] is True
            
            # Verify final state is consistent
            state = get_current_state()
            is_valid, error_msg = _validate_game_state_consistency(state)
            assert is_valid is True, f"Final state corruption: {error_msg}"
    
    def test_state_recovery_after_corruption(self):
        """
        Test that the system can recover from state corruption.
        Expected result: get_current_state() detects corruption and resets.
        Mock values: Artificially corrupted state.
        Why: Verify robustness against state corruption.
        """
        # Create a corrupted state and set it directly
        corrupted_state = GameState(
            shoe=[Card(suit=Suit.hearts, rank=Rank.ace)] * 400,  # Impossible shoe count
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=100.0
        )
        set_current_state(corrupted_state)
        
        # Verify corruption is detected
        is_valid, error_msg = _validate_game_state_consistency(corrupted_state)
        assert is_valid is False
        
        # get_current_state should detect and fix corruption
        recovered_state = get_current_state()
        is_valid, error_msg = _validate_game_state_consistency(recovered_state)
        assert is_valid is True
        
        # Should be a fresh state
        assert len(recovered_state.player_hand.cards) == 0
        assert len(recovered_state.dealer_hand.cards) == 0
        assert recovered_state.bet == 0.0
        assert len(recovered_state.shoe) == 312
    
    @pytest.mark.asyncio
    async def test_atomic_operation_rollback_prevents_corruption(self):
        """
        Test that atomic operation rollback prevents partial state corruption.
        Expected result: Failed operations leave state unchanged.
        Mock values: Operations that fail during execution.
        Why: Verify atomic operations prevent the corruption that caused original bug.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Store initial state
        initial_state = get_current_state()
        initial_cards = len(initial_state.shoe)
        
        # Mock user manager for successful bet but failed dealing
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1000.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_user_manager.credit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Mock dealing to fail
            with patch('dealer_agent.tools.dealer.dealInitialHands') as mock_deal:
                mock_deal.return_value = {"success": False, "error": "Dealing failed"}
                
                # Attempt atomic operation
                result = await placeBetAndDealInitialHands(100.0, tool_context)
                
                # Should fail and rollback
                assert result["success"] is False
                assert "refunded" in result["error"].lower()
                
                # State should be unchanged
                final_state = get_current_state()
                assert len(final_state.shoe) == initial_cards  # No cards dealt
                assert len(final_state.player_hand.cards) == 0
                assert len(final_state.dealer_hand.cards) == 0
                assert final_state.bet == 0.0
                
                # Verify rollback was called
                mock_user_manager.credit_user_balance.assert_called_with("test_user", 100.0)
    
    def test_validation_error_messages_are_helpful(self):
        """
        Test that validation error messages provide helpful debugging information.
        Expected result: Clear, specific error messages for different validation failures.
        Mock values: Various invalid states.
        Why: Verify error messages help identify and fix issues quickly.
        """
        # Test processPlayerAction with different invalid states
        test_cases = [
            {
                "state": GameState(shoe=shuffleShoe(), bet=100.0),  # No hands
                "expected_error": "initial hands have not been dealt properly"
            },
            {
                "state": GameState(
                    shoe=shuffleShoe(),
                    player_hand=Hand(cards=[Card(suit=Suit.hearts, rank=Rank.king), Card(suit=Suit.spades, rank=Rank.five)]),
                    dealer_hand=Hand(cards=[Card(suit=Suit.diamonds, rank=Rank.ace), Card(suit=Suit.clubs, rank=Rank.ten)]),
                    bet=0.0  # No bet
                ),
                "expected_error": "no bet has been placed"
            },
            {
                "state": GameState(
                    shoe=shuffleShoe(),
                    player_hand=Hand(cards=[
                        Card(suit=Suit.hearts, rank=Rank.king),
                        Card(suit=Suit.spades, rank=Rank.queen),
                        Card(suit=Suit.diamonds, rank=Rank.five)  # Bust
                    ]),
                    dealer_hand=Hand(cards=[Card(suit=Suit.diamonds, rank=Rank.ace), Card(suit=Suit.clubs, rank=Rank.ten)]),
                    bet=100.0
                ),
                "expected_error": "already bust"
            }
        ]
        
        for test_case in test_cases:
            set_current_state(test_case["state"])
            result = processPlayerAction('hit')
            assert result["success"] is False
            assert test_case["expected_error"] in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_original_gameplay_sequence_with_fixes(self):
        """
        Test the exact sequence from the original gameplay log, but with our fixes.
        Expected result: All operations succeed without state corruption.
        Mock values: Mimic the original gameplay scenario.
        Why: Verify our fixes solve the original problem completely.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "encrypred8532", "session_id": "test_session"}
        
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1010.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # 1. "Bet 500" - using atomic operation
            result = await placeBetAndDealInitialHands(500.0, tool_context)
            assert result["success"] is True
            assert result["bet"] == 500.0
            
            # Store the dealt cards to verify consistency
            original_player_cards = result["player_hand"]["cards"].copy()
            original_dealer_up_card = result["dealer_up_card"]
            
            # 2. "Hit" - this should work correctly now
            hit_result = processPlayerAction('hit')
            assert hit_result["success"] is True
            
            # Verify the hand actually has the original cards plus one more
            assert len(hit_result["player_hand"]["cards"]) == 3
            
            # Verify the original cards are still there (not corrupted)
            new_cards = hit_result["player_hand"]["cards"]
            assert new_cards[0] == original_player_cards[0]
            assert new_cards[1] == original_player_cards[1]
            # Third card should be the hit card
            
            # 3. Display state should show consistent information
            display_result = await displayState(tool_context=tool_context)
            assert display_result["success"] is True
            assert len(display_result["player_hand"]["cards"]) == 3
            assert display_result["dealer_up_card"] == original_dealer_up_card
            
            # Verify no corruption occurred
            state = get_current_state()
            is_valid, error_msg = _validate_game_state_consistency(state)
            assert is_valid is True, f"State corruption detected: {error_msg}"
            
            # The player hand should NOT be just [4♥] like in the original bug
            player_total = display_result["player_hand"]["total"]
            assert player_total != 4  # This was the corrupted value in the original bug 