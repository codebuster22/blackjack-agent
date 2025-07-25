import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dealer_agent.tools.dealer import (
    startRoundWithBet, reset_game_state, get_current_state,
    GameStateValidationError, SessionError, InsufficientBalanceError
)

class TestStartRoundWithBet:
    """Test the ultimate atomic startRoundWithBet function."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_success(self, mock_service_manager):
        """Test successful round start with bet."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        # Provide enough return values for multiple calls to get_user_balance
        mock_user_manager.get_user_balance.side_effect = [1000.0, 1000.0, 975.0, 975.0]
        mock_user_manager.debit_user_balance.return_value = True
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(25.0, tool_context)
        
        # Verify success
        assert result["success"] is True
        assert result["bet"] == 25.0
        assert result["balance"] == 975.0
        assert "player_hand" in result
        assert "dealer_up_card" in result
        assert result["remaining_cards"] == 308  # 312 - 4 cards dealt
        assert result["round_started"] is True
        assert "New round started with $25.0 bet" in result["message"]
        
        # Verify database calls
        mock_user_manager.get_user_balance.assert_called()
        mock_user_manager.debit_user_balance.assert_called_once_with("test_user", 25.0)
        
        # Verify game state
        state = get_current_state()
        assert state.bet == 25.0
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        assert len(state.shoe) == 308
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_insufficient_balance(self, mock_service_manager):
        """Test round start failure due to insufficient balance."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.return_value = 100.0
        mock_user_manager.debit_user_balance.return_value = False  # Insufficient balance
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(150.0, tool_context)
        
        # Verify failure
        assert result["success"] is False
        assert "Insufficient balance" in result["error"]
        assert result["balance"] == 100.0
        
        # Verify game state was reset (no partial state)
        state = get_current_state()
        assert state.bet == 0.0
        assert len(state.player_hand.cards) == 0
        assert len(state.dealer_hand.cards) == 0
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_no_user_id(self, mock_service_manager):
        """Test round start failure when no user_id in context."""
        # Setup tool context without user_id
        tool_context = MagicMock()
        tool_context.state = {"session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(25.0, tool_context)
        
        # Verify failure
        assert result["success"] is False
        assert "User ID not found" in result["error"]
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    @patch('dealer_agent.tools.dealer.initialize_game')
    async def test_start_round_with_bet_initialization_fails(self, mock_init, mock_service_manager):
        """Test round start failure when game initialization fails."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.return_value = 1000.0
        mock_init.return_value = {"success": False, "error": "Initialization failed"}
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(25.0, tool_context)
        
        # Verify failure
        assert result["success"] is False
        assert "Failed to initialize game" in result["error"]
        assert result["balance"] == 1000.0
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    @patch('dealer_agent.tools.dealer.placeBetAndDealInitialHands')
    async def test_start_round_with_bet_bet_deal_fails(self, mock_bet_deal, mock_service_manager):
        """Test round start failure when bet/deal phase fails."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.return_value = 1000.0
        mock_bet_deal.return_value = {"success": False, "error": "Dealing failed"}
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(25.0, tool_context)
        
        # Verify failure
        assert result["success"] is False
        assert "Failed during bet/deal phase" in result["error"]
        assert result["balance"] == 1000.0
        
        # Verify state was reset
        state = get_current_state()
        assert len(state.shoe) == 312  # Fresh shoe from reset
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_validation_fails_after_dealing(self, mock_service_manager):
        """Test round start failure when final validation fails after dealing."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.side_effect = [1000.0, 1000.0, 975.0, 1000.0]  # Original, during bet, after debit, after credit
        mock_user_manager.debit_user_balance.return_value = True
        mock_user_manager.credit_user_balance.return_value = True
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock a scenario where dealing succeeds but validation fails
        with patch('dealer_agent.tools.dealer._validate_player_turn_ready') as mock_validate:
            mock_validate.return_value = False
            
            # Call function
            result = await startRoundWithBet(25.0, tool_context)
        
        # Verify failure with rollback
        assert result["success"] is False
        assert "Game state validation failed" in result["error"]
        assert result["balance"] == 1000.0  # Bet was refunded
        
        # Verify rollback was called
        mock_user_manager.credit_user_balance.assert_called_with("test_user", 25.0)
        
        # Verify state was reset
        state = get_current_state()
        assert state.bet == 0.0
        assert len(state.player_hand.cards) == 0
        assert len(state.dealer_hand.cards) == 0
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_exception_during_dealing(self, mock_service_manager):
        """Test round start failure when exception occurs during dealing."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.side_effect = [1000.0, 1000.0]  # Before and during operation
        mock_user_manager.debit_user_balance.return_value = True
        mock_user_manager.credit_user_balance.return_value = True
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Mock dealing to raise an exception
        with patch('dealer_agent.tools.dealer.placeBetAndDealInitialHands') as mock_bet_deal:
            mock_bet_deal.side_effect = Exception("Dealing exception")
            
            # Call function
            result = await startRoundWithBet(25.0, tool_context)
        
        # Verify failure with rollback
        assert result["success"] is False
        assert "Exception during bet/deal phase" in result["error"]
        assert result["balance"] == 1000.0
        
        # Verify rollback was attempted (best effort)
        mock_user_manager.credit_user_balance.assert_called_with("test_user", 25.0)
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_preserves_state_on_success(self, mock_service_manager):
        """Test that successful round start preserves correct game state."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.side_effect = [500.0, 500.0, 475.0, 475.0]
        mock_user_manager.debit_user_balance.return_value = True
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(25.0, tool_context)
        
        # Verify success
        assert result["success"] is True
        
        # Verify state consistency
        state = get_current_state()
        assert state.bet == 25.0
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        
        # Verify cards are valid
        for card in state.player_hand.cards + state.dealer_hand.cards:
            assert hasattr(card, 'suit')
            assert hasattr(card, 'rank')
        
        # Verify shoe integrity
        total_cards = len(state.shoe) + len(state.player_hand.cards) + len(state.dealer_hand.cards)
        assert total_cards == 312  # Six deck shoe
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_invalid_bet_amount(self, mock_service_manager):
        """Test round start failure with invalid bet amount."""
        # Setup mocks
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.return_value = 1000.0
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Test negative bet
        result = await startRoundWithBet(-10.0, tool_context)
        assert result["success"] is False
        assert "Bet amount must be positive" in result["error"]
        
        # Test zero bet
        result = await startRoundWithBet(0.0, tool_context)
        assert result["success"] is False
        assert "Bet amount must be positive" in result["error"]
        
        # Test non-multiple of 5
        result = await startRoundWithBet(23.0, tool_context)
        assert result["success"] is False
        assert "Bet amount must be a multiple of 5" in result["error"]
    
    @pytest.mark.asyncio
    @patch('dealer_agent.tools.dealer.service_manager')
    async def test_start_round_with_bet_handles_network_failure(self, mock_service_manager):
        """Test round start handles network/database failures gracefully."""
        # Setup mocks to simulate network failure
        mock_user_manager = AsyncMock()
        mock_service_manager.user_manager = mock_user_manager
        mock_user_manager.get_user_balance.side_effect = Exception("Network timeout")
        
        # Setup tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Call function
        result = await startRoundWithBet(25.0, tool_context)
        
        # Verify graceful failure
        assert result["success"] is False
        assert "Unexpected error in startRoundWithBet" in result["error"]
        assert result["balance"] is None  # original_balance wasn't set due to exception 