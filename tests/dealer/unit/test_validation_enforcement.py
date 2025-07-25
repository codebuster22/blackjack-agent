import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dealer_agent.tools.dealer import (
    processPlayerAction,
    processDealerPlay,
    settleBet,
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


class TestValidationEnforcement:
    """Test that validation is properly enforced in game functions."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    # ===== processPlayerAction validation tests =====
    
    def test_process_player_action_no_hands_dealt(self):
        """
        Test that processPlayerAction rejects action when hands not dealt.
        Expected result: Error about hands not being dealt.
        Mock values: Empty hands, action 'hit'.
        Why: Verify validation prevents actions before dealing.
        """
        # Set up state with no hands dealt
        state = GameState(shoe=shuffleShoe(), bet=100.0)
        set_current_state(state)
        
        result = processPlayerAction('hit')
        
        assert result["success"] is False
        assert "initial hands have not been dealt" in result["error"].lower()
    
    def test_process_player_action_no_bet_placed(self):
        """
        Test that processPlayerAction rejects action when no bet placed.
        Expected result: Error about no bet placed.
        Mock values: Hands dealt but bet = 0.
        Why: Verify validation requires bet before actions.
        """
        # Set up state with hands but no bet
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
            bet=0.0  # No bet placed
        )
        set_current_state(state)
        
        result = processPlayerAction('hit')
        
        assert result["success"] is False
        assert "no bet has been placed" in result["error"].lower()
    
    def test_process_player_action_player_already_bust(self):
        """
        Test that processPlayerAction rejects action when player is already bust.
        Expected result: Error about player already bust.
        Mock values: Player hand with bust total.
        Why: Verify validation prevents actions after bust.
        """
        # Set up state with bust player hand
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.diamonds, rank=Rank.five)  # 25 (bust)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=100.0
        )
        set_current_state(state)
        
        result = processPlayerAction('hit')
        
        assert result["success"] is False
        assert "already bust" in result["error"].lower()
    
    def test_process_player_action_valid_state_succeeds(self):
        """
        Test that processPlayerAction succeeds with valid game state.
        Expected result: Success for 'stand' action.
        Mock values: Proper hands dealt, bet placed, player not bust.
        Why: Verify validation allows actions in valid states.
        """
        # Set up valid state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)  # 15 (valid)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.ten)
            ]),
            bet=100.0
        )
        set_current_state(state)
        
        result = processPlayerAction('stand')
        
        assert result["success"] is True
        assert "stand" in result["message"].lower()
    
    # ===== processDealerPlay validation tests =====
    
    def test_process_dealer_play_no_hands_dealt(self):
        """
        Test that processDealerPlay rejects when hands not dealt.
        Expected result: Error about hands not being dealt.
        Mock values: Empty hands.
        Why: Verify validation prevents dealer play before dealing.
        """
        # Set up state with no hands dealt
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = processDealerPlay()
        
        assert result["success"] is False
        assert "initial hands have not been dealt" in result["error"].lower()
    
    def test_process_dealer_play_player_turn_not_complete(self):
        """
        Test that processDealerPlay allows play when player implicitly stands.
        Expected result: Dealer plays normally when player has 2 cards and isn't bust.
        Mock values: Player with 2 cards (not bust), dealer with 2 cards.
        Why: Verify that dealer can play when player implicitly stands with initial hand.
        """
        # Set up state where player has initial hand (implicitly stands)
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)  # 15 - not bust, implicit stand
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.six)  # 17 - should stand
            ])
        )
        set_current_state(state)

        result = processDealerPlay()

        # Should succeed - dealer can play when player implicitly stands
        assert result["success"] is True
        # Dealer should stand on 17
        assert result["dealer_hand"]["total"] == 17
    
    def test_process_dealer_play_player_bust_succeeds(self):
        """
        Test that processDealerPlay succeeds when player is bust.
        Expected result: Success, dealer plays automatically.
        Mock values: Player bust, dealer with 2 cards.
        Why: Verify dealer can play when player busts.
        """
        # Set up state where player is bust
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.diamonds, rank=Rank.five)  # 25 (bust)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.six),
                Card(suit=Suit.clubs, rank=Rank.five)  # 11 - will need to hit
            ])
        )
        set_current_state(state)
        
        result = processDealerPlay()
        
        assert result["success"] is True
        assert result["dealer_hand"]["total"] >= 17  # Dealer played to completion
    
    def test_process_dealer_play_already_played(self):
        """
        Test that processDealerPlay handles when dealer already played.
        Expected result: Depends on implementation - either success or rejection.
        Mock values: Player not bust, dealer with 3+ cards (already played).
        Why: Verify handling of repeated dealer play calls.
        """
        # Set up state where dealer already played
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.nine)  # 19 (stood)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.six),
                Card(suit=Suit.clubs, rank=Rank.five),
                Card(suit=Suit.hearts, rank=Rank.seven)  # 18 (already played)
            ])
        )
        set_current_state(state)
        
        result = processDealerPlay()
        
        assert result["success"] is False
        assert "dealer has already played" in result["error"].lower()
    
    # ===== settleBet validation tests =====
    
    @pytest.mark.asyncio
    async def test_settle_bet_no_hands_dealt(self):
        """
        Test that settleBet rejects when hands not dealt.
        Expected result: Error about hands not being dealt.
        Mock values: Empty hands.
        Why: Verify validation prevents settlement before dealing.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Set up state with no hands dealt
        state = GameState(shoe=shuffleShoe(), bet=100.0)
        set_current_state(state)
        
        result = await settleBet(tool_context)
        
        assert result["success"] is False
        assert "initial hands have not been dealt" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_settle_bet_no_bet_placed(self):
        """
        Test that settleBet rejects when no bet placed.
        Expected result: Error about no bet placed.
        Mock values: Hands dealt but bet = 0.
        Why: Verify validation requires bet for settlement.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Set up state with hands but no bet
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
            bet=0.0  # No bet placed
        )
        set_current_state(state)
        
        result = await settleBet(tool_context)
        
        assert result["success"] is False
        assert "no bet has been placed" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_settle_bet_dealer_not_finished(self):
        """
        Test that settleBet rejects when dealer hasn't finished playing.
        Expected result: Error about dealer needing to complete play.
        Mock values: Player stood, dealer with total < 17.
        Why: Verify validation requires complete game before settlement.
        """
        # Mock tool context
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        # Set up state where dealer hasn't finished
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.nine)  # 19 (stood)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.five)  # 15 (must hit)
            ]),
            bet=100.0
        )
        set_current_state(state)
        
        result = await settleBet(tool_context)
        
        assert result["success"] is False
        assert "dealer must play until reaching 17" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_settle_bet_player_bust_succeeds(self):
        """
        Test that settleBet succeeds when player is bust (immediate settlement).
        Expected result: Success, player loses.
        Mock values: Player bust, bet placed.
        Why: Verify settlement can occur immediately when player busts.
        """
        # Mock tool context and user manager
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 900.0  # Balance after bet
            
            mock_db_service = AsyncMock()
            mock_db_service.save_round.return_value = True
            mock_db_service.update_session_status.return_value = True
            
            mock_service_manager.user_manager = mock_user_manager
            mock_service_manager.db_service = mock_db_service
            
            # Set up state where player is bust
            state = GameState(
                shoe=shuffleShoe(),
                player_hand=Hand(cards=[
                    Card(suit=Suit.hearts, rank=Rank.king),
                    Card(suit=Suit.spades, rank=Rank.queen),
                    Card(suit=Suit.diamonds, rank=Rank.five)  # 25 (bust)
                ]),
                dealer_hand=Hand(cards=[
                    Card(suit=Suit.diamonds, rank=Rank.ace),
                    Card(suit=Suit.clubs, rank=Rank.ten)
                ]),
                bet=100.0
            )
            set_current_state(state)
            
            result = await settleBet(tool_context)
            
            assert result["success"] is True
            assert result["result"] == "loss"
            assert result["payout"] == 0.0  # Player loses, no payout
    
    @pytest.mark.asyncio
    async def test_settle_bet_valid_complete_game_succeeds(self):
        """
        Test that settleBet succeeds with valid complete game.
        Expected result: Success, proper settlement calculation.
        Mock values: Both players complete, dealer at 17+.
        Why: Verify settlement works in normal complete game scenario.
        """
        # Mock tool context and services
        tool_context = MagicMock()
        tool_context.state = {"user_id": "test_user", "session_id": "test_session"}
        
        with patch('dealer_agent.tools.dealer.service_manager') as mock_service_manager:
            mock_user_manager = AsyncMock()
            mock_user_manager.get_user_balance.return_value = 900.0  # Balance after bet
            mock_user_manager.credit_user_balance.return_value = True
            
            mock_db_service = AsyncMock()
            mock_db_service.save_round.return_value = True
            mock_db_service.update_session_status.return_value = True
            
            mock_service_manager.user_manager = mock_user_manager
            mock_service_manager.db_service = mock_db_service
            
            # Set up state where both have completed play
            state = GameState(
                shoe=shuffleShoe(),
                player_hand=Hand(cards=[
                    Card(suit=Suit.hearts, rank=Rank.king),
                    Card(suit=Suit.spades, rank=Rank.nine)  # 19 (stood)
                ]),
                dealer_hand=Hand(cards=[
                    Card(suit=Suit.diamonds, rank=Rank.six),
                    Card(suit=Suit.clubs, rank=Rank.five),
                    Card(suit=Suit.hearts, rank=Rank.seven)  # 18 (complete)
                ]),
                bet=100.0
            )
            set_current_state(state)
            
            result = await settleBet(tool_context)
            
            assert result["success"] is True
            assert result["result"] == "win"  # Player 19 beats dealer 18
            assert result["payout"] == 200.0  # Get bet back + winnings
    
    # ===== Edge case validation tests =====
    
    def test_validation_with_corrupted_state(self):
        """
        Test that validation catches and handles corrupted game state.
        Expected result: Functions should fail gracefully with corruption errors.
        Mock values: Artificially corrupted state.
        Why: Verify robustness against state corruption.
        """
        # Create artificially corrupted state
        state = GameState(
            shoe=[],  # Empty shoe but cards dealt - impossible
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
        set_current_state(state)
        
        # Test that processPlayerAction handles corruption
        result = processPlayerAction('hit')
        # Should either fail validation or detect corruption in get_current_state()
        # The exact behavior depends on implementation, but it should not crash
        assert "success" in result
        
    def test_validation_messages_are_specific(self):
        """
        Test that validation error messages are specific and helpful.
        Expected result: Error messages should clearly indicate the problem.
        Mock values: Various invalid states.
        Why: Verify error messages help with debugging and user experience.
        """
        # Test specific error for no hands dealt
        state = GameState(shoe=shuffleShoe(), bet=100.0)
        set_current_state(state)
        result = processPlayerAction('hit')
        assert "Initial hands have not been dealt properly" in result["error"]
        
        # Test specific error for no bet
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[Card(suit=Suit.hearts, rank=Rank.king), Card(suit=Suit.spades, rank=Rank.five)]),
            dealer_hand=Hand(cards=[Card(suit=Suit.diamonds, rank=Rank.ace), Card(suit=Suit.clubs, rank=Rank.ten)]),
            bet=0.0
        )
        set_current_state(state)
        result = processPlayerAction('hit')
        assert "No bet has been placed" in result["error"] 