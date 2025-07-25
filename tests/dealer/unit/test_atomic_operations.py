import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dealer_agent.tools.dealer import (
    placeBetAndDealInitialHands,
    GameState,
    shuffleShoe,
    Card,
    Suit,
    Rank,
    Hand,
    reset_game_state,
    get_current_state,
    set_current_state
)
from google.adk.tools.tool_context import ToolContext


class TestAtomicOperations:
    """Test the atomic operation functions."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_success(self):
        """
        Test successful atomic operation of placing bet and dealing hands.
        Expected result: Both operations succeed, returns comprehensive data.
        Mock values: Valid user balance, successful bet placement and dealing.
        Why: Verify atomic operation works correctly in happy path.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock service manager
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.side_effect = [1000.0, 900.0]  # First call returns 1000, second returns 900
            mock_user_manager.debit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Initialize game state
            state = GameState(shoe=shuffleShoe())
            set_current_state(state)
            
            result = await placeBetAndDealInitialHands(100.0, tool_context)
            
            assert result["success"] is True
            assert result["bet"] == 100.0
            assert result["balance"] == 900.0  # 1000 - 100
            assert "player_hand" in result
            assert "dealer_up_card" in result
            assert len(result["player_hand"]["cards"]) == 2
            assert result["remaining_cards"] == 308  # 312 - 4 cards dealt
            
            # Verify user manager was called correctly
            mock_user_manager.get_user_balance.assert_called_with("test_user")
            mock_user_manager.debit_user_balance.assert_called_with("test_user", 100.0)
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_insufficient_balance(self):
        """
        Test atomic operation when user has insufficient balance.
        Expected result: Bet placement fails, no dealing occurs.
        Mock values: Insufficient user balance.
        Why: Verify atomic operation fails gracefully when bet can't be placed.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock service manager - insufficient balance
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 50.0
            mock_user_manager.debit_user_balance.return_value = False  # Insufficient balance
            mock_service_manager.user_manager = mock_user_manager
            
            # Initialize game state
            state = GameState(shoe=shuffleShoe())
            set_current_state(state)
            
            result = await placeBetAndDealInitialHands(100.0, tool_context)
            
            assert result["success"] is False
            assert "error" in result
            assert "balance" in result["error"].lower() or "insufficient" in result["error"].lower()
            
            # Verify dealing didn't occur - game state should be unchanged
            current_state = get_current_state()
            assert len(current_state.player_hand.cards) == 0
            assert len(current_state.dealer_hand.cards) == 0
            assert current_state.bet == 0.0
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_dealing_fails(self):
        """
        Test atomic operation when dealing fails after successful bet.
        Expected result: Bet is rolled back, error is returned.
        Mock values: Successful bet, but dealing failure.
        Why: Verify rollback mechanism works when dealing fails.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock service manager
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1000.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_user_manager.credit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Create a state that will cause dealing to fail (empty shoe)
            state = GameState(shoe=[])  # Empty shoe will cause dealing to fail
            set_current_state(state)
            
            result = await placeBetAndDealInitialHands(100.0, tool_context)
            
            assert result["success"] is False
            assert "error" in result
            assert "refunded" in result["error"].lower()
            assert result["balance"] == 1000.0  # Original balance restored
            
            # Verify rollback occurred
            mock_user_manager.credit_user_balance.assert_called_with("test_user", 100.0)
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_validation_fails(self):
        """
        Test atomic operation when post-dealing validation fails.
        Expected result: Bet is rolled back, game state is reset.
        Mock values: Successful bet and dealing, but invalid resulting state.
        Why: Verify validation catches corruption and triggers rollback.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock service manager
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1000.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_user_manager.credit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Mock validation to fail
            with patch('dealer_agent.tools.dealer._validate_player_turn_ready') as mock_validate:
                mock_validate.return_value = False
                
                # Initialize game state
                state = GameState(shoe=shuffleShoe())
                set_current_state(state)
                
                result = await placeBetAndDealInitialHands(100.0, tool_context)
                
                assert result["success"] is False
                assert "validation failed" in result["error"].lower()
                assert "refunded" in result["error"].lower()
                assert result["balance"] == 1000.0  # Original balance restored
                
                # Verify rollback occurred
                mock_user_manager.credit_user_balance.assert_called_with("test_user", 100.0)
                
                # Verify game state was reset
                current_state = get_current_state()
                assert len(current_state.player_hand.cards) == 0
                assert len(current_state.dealer_hand.cards) == 0
                assert current_state.bet == 0.0
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_no_user_id(self):
        """
        Test atomic operation when user_id is missing from context.
        Expected result: Error about missing user ID.
        Mock values: Tool context without user_id.
        Why: Verify proper error handling for invalid context.
        """
        # Mock tool context without user_id
        tool_context = MagicMock()
        tool_context.state = {"session_id": "test_session"}  # Missing user_id
        
        result = await placeBetAndDealInitialHands(100.0, tool_context)
        
        assert result["success"] is False
        assert "user id" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_exception_during_dealing(self):
        """
        Test atomic operation when exception occurs during dealing phase.
        Expected result: Bet is rolled back, exception is handled gracefully.
        Mock values: Successful bet, but exception during dealing.
        Why: Verify exception handling and rollback for unexpected errors.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock service manager
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1000.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_user_manager.credit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Mock dealInitialHands to raise an exception
            with patch('dealer_agent.tools.dealer.dealInitialHands') as mock_deal:
                mock_deal.side_effect = Exception("Dealing system error")
                
                # Initialize game state
                state = GameState(shoe=shuffleShoe())
                set_current_state(state)
                
                result = await placeBetAndDealInitialHands(100.0, tool_context)
                
                assert result["success"] is False
                assert "failed during dealing phase" in result["error"].lower()
                assert "refunded" in result["error"].lower()
                assert result["balance"] == 1000.0  # Original balance restored
                
                # Verify rollback occurred
                mock_user_manager.credit_user_balance.assert_called_with("test_user", 100.0)
    
    @pytest.mark.asyncio
    async def test_place_bet_and_deal_initial_hands_preserves_state_on_success(self):
        """
        Test that successful atomic operation properly preserves game state.
        Expected result: Game state contains proper bet, hands, and shoe count.
        Mock values: Successful operation.
        Why: Verify state is properly maintained after successful atomic operation.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock service manager
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 1000.0
            mock_user_manager.debit_user_balance.return_value = True
            mock_service_manager.user_manager = mock_user_manager
            
            # Initialize game state
            initial_shoe_count = 312
            state = GameState(shoe=shuffleShoe())
            set_current_state(state)
            
            result = await placeBetAndDealInitialHands(100.0, tool_context)
            
            assert result["success"] is True
            
            # Verify final state
            final_state = get_current_state()
            assert final_state.bet == 100.0
            assert len(final_state.player_hand.cards) == 2
            assert len(final_state.dealer_hand.cards) == 2
            assert len(final_state.shoe) == initial_shoe_count - 4  # 4 cards dealt
            
            # Verify state consistency
            total_cards = len(final_state.shoe) + len(final_state.player_hand.cards) + len(final_state.dealer_hand.cards)
            assert total_cards == 312 