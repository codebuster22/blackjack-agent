import pytest
from unittest.mock import Mock
from dealer_agent.tools.dealer import (
    settleBet, GameState, Hand, Card, Suit, Rank, shuffleShoe, 
    set_current_state, placeBet, reset_game_state
)


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
@pytest.mark.asyncio
class TestSettleBetIntegration:
    """Integration tests for settleBet function with database."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    async def test_player_bust(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when player busts.
        Expected result: Payout = 0, result = 'loss'.
        Mock values: Player hand bust (24), dealer hand valid (18), bet = 100.
        Why: Verify player loses when they bust regardless of dealer's hand.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=100.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.nine),
                Card(suit=Suit.clubs, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.hearts, rank=Rank.eight)
            ])
        )
        set_current_state(state)
        
        # Place bet first (required for database operations)
        await placeBet(100.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 0.0
        assert result["result"] == 'loss'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_dealer_bust(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when dealer busts but player doesn't.
        Expected result: Payout = +bet*2, result = 'win'.
        Mock values: Player hand valid (18), dealer hand bust (23), bet = 50.
        Why: Verify player wins when dealer busts and player doesn't.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=50.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.eight)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.nine),
                Card(suit=Suit.hearts, rank=Rank.four)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(50.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 100.0  # bet back + equal winnings
        assert result["result"] == 'win'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_player_blackjack(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when player has blackjack and dealer doesn't.
        Expected result: Payout = +bet*2.5, result = 'win'.
        Mock values: Player blackjack (A+K), dealer not blackjack (10+7), bet = 100.
        Why: Verify blackjack pays 3:2 (1.5× bet).
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=100.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.diamonds, rank=Rank.king)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.seven)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(100.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 250.0  # bet back + 1.5x winnings
        assert result["result"] == 'win'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_dealer_blackjack(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when dealer has blackjack and player doesn't.
        Expected result: Payout = 0, result = 'loss'.
        Mock values: Dealer blackjack (A+Q), player not blackjack (10+8), bet = 75.
        Why: Verify player loses when dealer has blackjack and they don't.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=75.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.eight)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.queen)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(75.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 0.0
        assert result["result"] == 'loss'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_mutual_blackjack_push(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when both player and dealer have blackjack.
        Expected result: Payout = +bet, result = 'push'.
        Mock values: Both blackjack (A+K), bet = 50.
        Why: Verify push when both have blackjack.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=50.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.diamonds, rank=Rank.king)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.king)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(50.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 50.0  # bet back
        assert result["result"] == 'push'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_higher_total_wins(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when player has higher total.
        Expected result: Payout = +bet*2, result = 'win'.
        Mock values: Player 20, dealer 18, bet = 25.
        Why: Verify player wins with higher total.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=25.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.ten)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.eight)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(25.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 50.0  # bet back + equal winnings
        assert result["result"] == 'win'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    @pytest.mark.asyncio
    async def test_lower_total_loses(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when player has lower total.
        Expected result: Payout = 0, result = 'loss'.
        Mock values: Player 16, dealer 19, bet = 40.
        Why: Verify player loses with lower total.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=40.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.six)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.nine)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(40.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 0.0
        assert result["result"] == 'loss'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_equal_total_push(self, clean_database, mock_tool_context_with_data):
        """
        Test settlement when player and dealer have equal totals.
        Expected result: Payout = +bet, result = 'push'.
        Mock values: Both 17, bet = 30.
        Why: Verify push when totals are equal.
        """
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=30.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.seven)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.seven)
            ])
        )
        set_current_state(state)
        
        # Place bet first
        await placeBet(30.0, mock_tool_context_with_data)
        
        result = await settleBet(mock_tool_context_with_data)
        
        assert result["success"] is True
        assert result["payout"] == 30.0  # bet back
        assert result["result"] == 'push'
        assert result["round_saved"] is True
        assert result["session_completed"] is True
    
    async def test_missing_user_id_raises_error(self, clean_database):
        """
        Test that missing user_id in ToolContext raises error.
        Expected result: Error response with session error.
        Mock values: ToolContext without user_id.
        Why: Ensure proper error handling for missing context.
        """
        # Create mock context without user_id
        mock_context = Mock()
        mock_context.state = {
            "session_id": "test_session_id"
            # Missing user_id
        }
        
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=25.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.king)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.six)
            ])
        )
        set_current_state(state)
        
        result = await settleBet(mock_context)
        
        assert result["success"] is False
        assert "session error" in result["error"].lower()
    
    async def test_missing_session_id_raises_error(self, clean_database):
        """
        Test that missing session_id in ToolContext raises error.
        Expected result: Error response with session error.
        Mock values: ToolContext without session_id.
        Why: Ensure proper error handling for missing context.
        """
        # Create mock context without session_id
        mock_context = Mock()
        mock_context.state = {
            "user_id": "test_user_id"
            # Missing session_id
        }
        
        # Setup game state
        state = GameState(
            shoe=shuffleShoe(),
            bet=25.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.king)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.six)
            ])
        )
        set_current_state(state)
        
        result = await settleBet(mock_context)
        
        assert result["success"] is False
        assert "session error" in result["error"].lower() 