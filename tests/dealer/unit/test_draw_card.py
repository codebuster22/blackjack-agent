import pytest
from dealer_agent.tools.dealer import drawCard, Card, Suit, Rank


class TestDrawCard:
    """Test cases for drawCard() function."""
    
    def test_pop_behavior(self):
        """
        Test that drawCard() removes and returns the last card from the shoe.
        Expected result: Returns the last card and reduces shoe size by 1.
        Mock values: Small shoe with 2 known cards.
        Why: Verify the card drawing mechanism works correctly.
        """
        # Create a small test shoe
        test_shoe = [
            Card(suit=Suit.hearts, rank=Rank.ace),
            Card(suit=Suit.diamonds, rank=Rank.king)
        ]
        original_size = len(test_shoe)
        last_card = test_shoe[-1]
        
        card, new_shoe = drawCard(test_shoe)
        
        # Check returned card matches last card
        assert card == last_card
        # Check shoe size reduced by 1
        assert len(new_shoe) == original_size - 1
        # Check the returned shoe doesn't contain the drawn card
        assert card not in new_shoe
    
    def test_empty_shoe(self):
        """
        Test that drawCard() raises an exception when shoe is empty.
        Expected result: IndexError when trying to draw from empty shoe.
        Mock values: Empty list as shoe.
        Why: Ensure proper error handling when no cards are available.
        """
        empty_shoe = []
        
        with pytest.raises(IndexError):
            drawCard(empty_shoe) 