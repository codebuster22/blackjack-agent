import pytest
from dealer_agent.tools.dealer import dealInitialHands, GameState, Card, Suit, Rank, shuffleShoe


class TestDealInitialHands:
    """Test cases for dealInitialHands() function."""
    
    def test_proper_dealing(self):
        """
        Test that dealInitialHands() deals exactly 2 cards to each player and dealer.
        Expected result: 2 cards each, bet set to 50, shoe reduced by 4 cards.
        Mock values: Fresh shuffled shoe, empty hands, bet=50.
        Why: Verify initial dealing follows blackjack rules.
        """
        state = GameState(shoe=shuffleShoe())
        original_shoe_size = len(state.shoe)
        
        state = dealInitialHands(state)
        
        # Check bet is set (bet should be set before calling dealInitialHands)
        # Note: dealInitialHands doesn't set bet, it only deals cards
        # Check each hand has 2 cards
        assert len(state.player_hand.cards) == 2
        assert len(state.dealer_hand.cards) == 2
        # Check shoe reduced by 4 cards
        assert len(state.shoe) == original_shoe_size - 4
    
    def test_alternating_deal_order(self):
        """
        Test that cards are dealt in alternating order (player, dealer, player, dealer).
        Expected result: First card to player, second to dealer, etc.
        Mock values: Known shoe with specific card order.
        Why: Verify dealing follows standard blackjack dealing order.
        """
        # Create a shoe with known card order (cards are drawn from the end)
        # So we need to put the expected cards at the end
        extra_cards = shuffleShoe()
        known_shoe = extra_cards + [
            Card(suit=Suit.spades, rank=Rank.jack),   # 2nd to dealer (drawn first)
            Card(suit=Suit.clubs, rank=Rank.queen),   # 2nd to player
            Card(suit=Suit.diamonds, rank=Rank.king), # 1st to dealer
            Card(suit=Suit.hearts, rank=Rank.ace),    # 1st to player (drawn last)
        ]
        
        state = GameState(shoe=known_shoe)
        state = dealInitialHands(state)
        
        # Check alternating deal order
        assert state.player_hand.cards[0] == Card(suit=Suit.hearts, rank=Rank.ace)
        assert state.dealer_hand.cards[0] == Card(suit=Suit.diamonds, rank=Rank.king)
        assert state.player_hand.cards[1] == Card(suit=Suit.clubs, rank=Rank.queen)
        assert state.dealer_hand.cards[1] == Card(suit=Suit.spades, rank=Rank.jack) 