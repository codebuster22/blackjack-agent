"""
Unit tests for database service utilities.
"""
import pytest
from services.card_utils import card_to_string, string_to_card, hand_to_string, string_to_hand
from dealer_agent.tools.dealer import Card, Hand, Suit, Rank


@pytest.mark.unit
class TestCardConversion:
    """Test card conversion utilities."""
    
    def test_card_to_string(self):
        """Test card to string conversion."""
        # Test ace of hearts
        card = Card(suit=Suit.hearts, rank=Rank.ace)
        card_str = card_to_string(card)
        assert card_str == "AH"
        
        # Test king of spades
        card = Card(suit=Suit.spades, rank=Rank.king)
        card_str = card_to_string(card)
        assert card_str == "KS"
        
        # Test ten of diamonds
        card = Card(suit=Suit.diamonds, rank=Rank.ten)
        card_str = card_to_string(card)
        assert card_str == "10D"
        
        # Test two of clubs
        card = Card(suit=Suit.clubs, rank=Rank.two)
        card_str = card_to_string(card)
        assert card_str == "2C"
    
    def test_string_to_card(self):
        """Test string to card conversion."""
        # Test ace of hearts
        card_str = "AH"
        card = string_to_card(card_str)
        assert card.suit == Suit.hearts
        assert card.rank == Rank.ace
        
        # Test king of spades
        card_str = "KS"
        card = string_to_card(card_str)
        assert card.suit == Suit.spades
        assert card.rank == Rank.king
        
        # Test ten of diamonds
        card_str = "10D"
        card = string_to_card(card_str)
        assert card.suit == Suit.diamonds
        assert card.rank == Rank.ten
        
        # Test two of clubs
        card_str = "2C"
        card = string_to_card(card_str)
        assert card.suit == Suit.clubs
        assert card.rank == Rank.two
    
    def test_card_roundtrip(self):
        """Test card conversion roundtrip (card -> string -> card)."""
        # Test various cards
        test_cards = [
            Card(suit=Suit.hearts, rank=Rank.ace),
            Card(suit=Suit.spades, rank=Rank.king),
            Card(suit=Suit.diamonds, rank=Rank.ten),
            Card(suit=Suit.clubs, rank=Rank.two),
            Card(suit=Suit.hearts, rank=Rank.queen),
            Card(suit=Suit.spades, rank=Rank.jack),
        ]
        
        for original_card in test_cards:
            card_str = card_to_string(original_card)
            converted_card = string_to_card(card_str)
            
            assert converted_card.suit == original_card.suit
            assert converted_card.rank == original_card.rank
    
    def test_hand_to_string(self):
        """Test hand to string conversion."""
        # Test hand with two cards
        hand = Hand(cards=[
            Card(suit=Suit.spades, rank=Rank.king),
            Card(suit=Suit.hearts, rank=Rank.ace)
        ])
        hand_str = hand_to_string(hand)
        assert hand_str == '["KS", "AH"]'
        
        # Test hand with three cards
        hand = Hand(cards=[
            Card(suit=Suit.diamonds, rank=Rank.ten),
            Card(suit=Suit.clubs, rank=Rank.five),
            Card(suit=Suit.hearts, rank=Rank.queen)
        ])
        hand_str = hand_to_string(hand)
        assert hand_str == '["10D", "5C", "QH"]'
        
        # Test empty hand
        hand = Hand(cards=[])
        hand_str = hand_to_string(hand)
        assert hand_str == '[]'
    
    def test_string_to_hand(self):
        """Test string to hand conversion."""
        # Test hand with two cards
        hand_str = '["KS", "AH"]'
        hand = string_to_hand(hand_str)
        assert len(hand.cards) == 2
        assert hand.cards[0].suit == Suit.spades
        assert hand.cards[0].rank == Rank.king
        assert hand.cards[1].suit == Suit.hearts
        assert hand.cards[1].rank == Rank.ace
        
        # Test hand with three cards
        hand_str = '["10D", "5C", "QH"]'
        hand = string_to_hand(hand_str)
        assert len(hand.cards) == 3
        assert hand.cards[0].suit == Suit.diamonds
        assert hand.cards[0].rank == Rank.ten
        assert hand.cards[1].suit == Suit.clubs
        assert hand.cards[1].rank == Rank.five
        assert hand.cards[2].suit == Suit.hearts
        assert hand.cards[2].rank == Rank.queen
        
        # Test empty hand
        hand_str = '[]'
        hand = string_to_hand(hand_str)
        assert len(hand.cards) == 0
    
    def test_hand_roundtrip(self):
        """Test hand conversion roundtrip (hand -> string -> hand)."""
        # Test various hands
        test_hands = [
            Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.king),
                Card(suit=Suit.hearts, rank=Rank.ace)
            ]),
            Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.five),
                Card(suit=Suit.hearts, rank=Rank.queen)
            ]),
            Hand(cards=[]),
        ]
        
        for original_hand in test_hands:
            hand_str = hand_to_string(original_hand)
            converted_hand = string_to_hand(hand_str)
            
            assert len(converted_hand.cards) == len(original_hand.cards)
            
            for i, card in enumerate(original_hand.cards):
                assert converted_hand.cards[i].suit == card.suit
                assert converted_hand.cards[i].rank == card.rank 