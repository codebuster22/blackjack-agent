import pytest
from dealer_agent.tools.dealer import processDealerPlay, GameState, shuffleShoe, Card, Suit, Rank, Hand, reset_game_state


class TestProcessDealerPlay:
    """Test the processDealerPlay function."""
    
    def setup_method(self):
        """Reset game state before each test."""
        reset_game_state()
    
    def test_dealer_hits_up_to_17(self):
        """
        Test that dealer draws cards until total >= 17.
        Expected result: Dealer draws cards until total reaches or exceeds 17.
        Mock values: Dealer hand with total 12.
        Why: Verify dealer follows standard blackjack rules of hitting on 16 and below.
        """
        # Initialize game state with player turn complete (bust or stood)
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.clubs, rank=Rank.five)  # 25 - bust, so dealer can play
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.two)
            ])
        )
        set_current_state(state)
        
        result = processDealerPlay()
        
        assert result["success"] is True
        assert result["dealer_hand"]["total"] >= 17
        assert len(result["dealer_hand"]["cards"]) >= 3  # Should have drawn at least 1 more card
    
    def test_soft_17_stand(self):
        """
        Test that dealer stands on soft 17 (A+6).
        Expected result: No additional cards drawn when dealer has soft 17.
        Mock values: Dealer hand with [A, 6] (soft 17).
        Why: Verify dealer follows soft 17 rule correctly.
        """
        # Initialize game state with player turn complete (bust)
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.clubs, rank=Rank.two)  # 22 - bust, so dealer can play
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.diamonds, rank=Rank.six)
            ])
        )
        set_current_state(state)
        
        result = processDealerPlay()
        
        assert result["success"] is True
        assert result["dealer_hand"]["total"] == 17  # Should still be 17 (soft)
        assert len(result["dealer_hand"]["cards"]) == 2  # No additional cards drawn
    
    def test_immediate_stand_on_17_plus(self):
        """
        Test that dealer stands immediately when total >= 17.
        Expected result: No cards drawn when dealer already has 17 or higher.
        Mock values: Dealer hand with [10, 7] (total 17).
        Why: Verify dealer doesn't draw unnecessarily when already at or above 17.
        """
        # Initialize game state with player turn complete (bust)
        from dealer_agent.tools.dealer import set_current_state
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.jack),
                Card(suit=Suit.spades, rank=Rank.queen),
                Card(suit=Suit.clubs, rank=Rank.three)  # 23 - bust, so dealer can play
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.seven)
            ])
        )
        set_current_state(state)
        
        result = processDealerPlay()
        
        assert result["success"] is True
        assert result["dealer_hand"]["total"] == 17  # Should still be 17
        assert len(result["dealer_hand"]["cards"]) == 2  # No additional cards drawn 