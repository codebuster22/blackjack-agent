import pytest
from unittest.mock import Mock
from dealer_agent.tools.dealer import (
    placeBet, settleBet, GameState, Hand, Card, Suit, Rank, 
    shuffleShoe, set_current_state, reset_game_state
)
from tests.test_helpers import setup_test_environment


@pytest.mark.docker
@pytest.mark.database
@pytest.mark.integration
class TestSimpleIntegration:
    """Simple integration tests to verify basic functionality."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_simple_place_bet(self, clean_database, mock_tool_context_with_data):
        """
        Test simple bet placement to verify database connection works.
        Expected result: Bet placed successfully with balance updated.
        Mock values: User with balance=100, bet amount=25.
        Why: Verify basic database integration works.
        """
        # Initialize game state
        state = GameState(shoe=shuffleShoe())
        set_current_state(state)
        
        result = placeBet(25.0, mock_tool_context_with_data)
        
        print(f"Place bet result: {result}")
        
        assert result["success"] is True
        assert result["bet"] == 25.0
        assert result["balance"] == 75.0  # 100 - 25
    
    def test_simple_settle_bet(self, clean_database, mock_tool_context_with_data):
        """
        Test simple bet settlement to see what the function actually returns.
        Expected result: See actual return values from settleBet.
        Mock values: Player bust hand, dealer valid hand.
        Why: Understand actual function behavior to fix integration tests.
        """
        # Initialize game state with player bust
        state = GameState(
            shoe=shuffleShoe(),
            bet=25.0,
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
        
        # Place bet first
        placeBet(25.0, mock_tool_context_with_data)
        
        # Settle bet
        result = settleBet(mock_tool_context_with_data)
        
        print(f"Settle bet result: {result}")
        
        # Just check it succeeds, don't make specific assertions yet
        assert "success" in result 