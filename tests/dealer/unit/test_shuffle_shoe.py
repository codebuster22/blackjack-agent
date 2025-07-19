import pytest
from dealer_agent.tools.dealer import shuffleShoe, Suit, Rank


class TestShuffleShoe:
    """Test cases for shuffleShoe() function."""
    
    def test_six_deck_composition(self):
        """
        Test that shuffleShoe() returns exactly 312 cards (6 decks × 52 cards).
        Expected result: 312 Card objects with exactly 6 of each unique (suit, rank) combination.
        Mock values: None - using actual function to generate shoe.
        Why: Verify the shoe contains the correct number of cards for a six-deck game.
        """
        shoe = shuffleShoe()
        
        # Check total number of cards
        assert len(shoe) == 312
        
        # Check exactly 6 of each card
        card_counts = {}
        for card in shoe:
            key = (card.suit, card.rank)
            card_counts[key] = card_counts.get(key, 0) + 1
        
        # Verify 6 of each card
        for suit in Suit:
            for rank in Rank:
                assert card_counts[(suit, rank)] == 6
    
    def test_randomness(self):
        """
        Test that shuffleShoe() produces different card orders on multiple calls.
        Expected result: Two consecutive calls should produce different card orders.
        Mock values: None - using actual function to generate shoes.
        Why: Ensure the shoe is properly shuffled and not deterministic.
        """
        shoe1 = shuffleShoe()
        shoe2 = shuffleShoe()
        
        # Check that the orders are different (very high probability)
        # Convert to string representation for comparison
        shoe1_str = [f"{card.rank}{card.suit}" for card in shoe1[:10]]  # First 10 cards
        shoe2_str = [f"{card.rank}{card.suit}" for card in shoe2[:10]]
        
        assert shoe1_str != shoe2_str 