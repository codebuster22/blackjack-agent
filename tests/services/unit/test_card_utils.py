"""
Unit tests for card utilities.
Tests pure logic without database dependencies.
"""
import pytest
import json
from services.card_utils import (
    card_to_string, string_to_card, hand_to_string, string_to_hand,
    hand_to_dict, dict_to_hand
)
from dealer_agent.tools.dealer import Card, Hand, Suit, Rank


@pytest.mark.unit
class TestCardConversion:
    """Test card conversion utilities."""
    
    def test_card_to_string_all_cards(self):
        """Test card to string conversion for all cards."""
        # Test all ranks and suits
        test_cases = [
            (Card(suit=Suit.hearts, rank=Rank.ace), "AH"),
            (Card(suit=Suit.diamonds, rank=Rank.ace), "AD"),
            (Card(suit=Suit.clubs, rank=Rank.ace), "AC"),
            (Card(suit=Suit.spades, rank=Rank.ace), "AS"),
            (Card(suit=Suit.hearts, rank=Rank.king), "KH"),
            (Card(suit=Suit.diamonds, rank=Rank.king), "KD"),
            (Card(suit=Suit.clubs, rank=Rank.king), "KC"),
            (Card(suit=Suit.spades, rank=Rank.king), "KS"),
            (Card(suit=Suit.hearts, rank=Rank.queen), "QH"),
            (Card(suit=Suit.diamonds, rank=Rank.queen), "QD"),
            (Card(suit=Suit.clubs, rank=Rank.queen), "QC"),
            (Card(suit=Suit.spades, rank=Rank.queen), "QS"),
            (Card(suit=Suit.hearts, rank=Rank.jack), "JH"),
            (Card(suit=Suit.diamonds, rank=Rank.jack), "JD"),
            (Card(suit=Suit.clubs, rank=Rank.jack), "JC"),
            (Card(suit=Suit.spades, rank=Rank.jack), "JS"),
            (Card(suit=Suit.hearts, rank=Rank.ten), "10H"),
            (Card(suit=Suit.diamonds, rank=Rank.ten), "10D"),
            (Card(suit=Suit.clubs, rank=Rank.ten), "10C"),
            (Card(suit=Suit.spades, rank=Rank.ten), "10S"),
            (Card(suit=Suit.hearts, rank=Rank.nine), "9H"),
            (Card(suit=Suit.diamonds, rank=Rank.nine), "9D"),
            (Card(suit=Suit.clubs, rank=Rank.nine), "9C"),
            (Card(suit=Suit.spades, rank=Rank.nine), "9S"),
            (Card(suit=Suit.hearts, rank=Rank.eight), "8H"),
            (Card(suit=Suit.diamonds, rank=Rank.eight), "8D"),
            (Card(suit=Suit.clubs, rank=Rank.eight), "8C"),
            (Card(suit=Suit.spades, rank=Rank.eight), "8S"),
            (Card(suit=Suit.hearts, rank=Rank.seven), "7H"),
            (Card(suit=Suit.diamonds, rank=Rank.seven), "7D"),
            (Card(suit=Suit.clubs, rank=Rank.seven), "7C"),
            (Card(suit=Suit.spades, rank=Rank.seven), "7S"),
            (Card(suit=Suit.hearts, rank=Rank.six), "6H"),
            (Card(suit=Suit.diamonds, rank=Rank.six), "6D"),
            (Card(suit=Suit.clubs, rank=Rank.six), "6C"),
            (Card(suit=Suit.spades, rank=Rank.six), "6S"),
            (Card(suit=Suit.hearts, rank=Rank.five), "5H"),
            (Card(suit=Suit.diamonds, rank=Rank.five), "5D"),
            (Card(suit=Suit.clubs, rank=Rank.five), "5C"),
            (Card(suit=Suit.spades, rank=Rank.five), "5S"),
            (Card(suit=Suit.hearts, rank=Rank.four), "4H"),
            (Card(suit=Suit.diamonds, rank=Rank.four), "4D"),
            (Card(suit=Suit.clubs, rank=Rank.four), "4C"),
            (Card(suit=Suit.spades, rank=Rank.four), "4S"),
            (Card(suit=Suit.hearts, rank=Rank.three), "3H"),
            (Card(suit=Suit.diamonds, rank=Rank.three), "3D"),
            (Card(suit=Suit.clubs, rank=Rank.three), "3C"),
            (Card(suit=Suit.spades, rank=Rank.three), "3S"),
            (Card(suit=Suit.hearts, rank=Rank.two), "2H"),
            (Card(suit=Suit.diamonds, rank=Rank.two), "2D"),
            (Card(suit=Suit.clubs, rank=Rank.two), "2C"),
            (Card(suit=Suit.spades, rank=Rank.two), "2S"),
        ]
        
        for card, expected in test_cases:
            result = card_to_string(card)
            assert result == expected, f"Failed for {card.rank.value}{card.suit.value}"
    
    def test_string_to_card_all_cards(self):
        """Test string to card conversion for all cards."""
        # Test all ranks and suits
        test_cases = [
            ("AH", Card(suit=Suit.hearts, rank=Rank.ace)),
            ("AD", Card(suit=Suit.diamonds, rank=Rank.ace)),
            ("AC", Card(suit=Suit.clubs, rank=Rank.ace)),
            ("AS", Card(suit=Suit.spades, rank=Rank.ace)),
            ("KH", Card(suit=Suit.hearts, rank=Rank.king)),
            ("KD", Card(suit=Suit.diamonds, rank=Rank.king)),
            ("KC", Card(suit=Suit.clubs, rank=Rank.king)),
            ("KS", Card(suit=Suit.spades, rank=Rank.king)),
            ("QH", Card(suit=Suit.hearts, rank=Rank.queen)),
            ("QD", Card(suit=Suit.diamonds, rank=Rank.queen)),
            ("QC", Card(suit=Suit.clubs, rank=Rank.queen)),
            ("QS", Card(suit=Suit.spades, rank=Rank.queen)),
            ("JH", Card(suit=Suit.hearts, rank=Rank.jack)),
            ("JD", Card(suit=Suit.diamonds, rank=Rank.jack)),
            ("JC", Card(suit=Suit.clubs, rank=Rank.jack)),
            ("JS", Card(suit=Suit.spades, rank=Rank.jack)),
            ("10H", Card(suit=Suit.hearts, rank=Rank.ten)),
            ("10D", Card(suit=Suit.diamonds, rank=Rank.ten)),
            ("10C", Card(suit=Suit.clubs, rank=Rank.ten)),
            ("10S", Card(suit=Suit.spades, rank=Rank.ten)),
            ("9H", Card(suit=Suit.hearts, rank=Rank.nine)),
            ("9D", Card(suit=Suit.diamonds, rank=Rank.nine)),
            ("9C", Card(suit=Suit.clubs, rank=Rank.nine)),
            ("9S", Card(suit=Suit.spades, rank=Rank.nine)),
            ("8H", Card(suit=Suit.hearts, rank=Rank.eight)),
            ("8D", Card(suit=Suit.diamonds, rank=Rank.eight)),
            ("8C", Card(suit=Suit.clubs, rank=Rank.eight)),
            ("8S", Card(suit=Suit.spades, rank=Rank.eight)),
            ("7H", Card(suit=Suit.hearts, rank=Rank.seven)),
            ("7D", Card(suit=Suit.diamonds, rank=Rank.seven)),
            ("7C", Card(suit=Suit.clubs, rank=Rank.seven)),
            ("7S", Card(suit=Suit.spades, rank=Rank.seven)),
            ("6H", Card(suit=Suit.hearts, rank=Rank.six)),
            ("6D", Card(suit=Suit.diamonds, rank=Rank.six)),
            ("6C", Card(suit=Suit.clubs, rank=Rank.six)),
            ("6S", Card(suit=Suit.spades, rank=Rank.six)),
            ("5H", Card(suit=Suit.hearts, rank=Rank.five)),
            ("5D", Card(suit=Suit.diamonds, rank=Rank.five)),
            ("5C", Card(suit=Suit.clubs, rank=Rank.five)),
            ("5S", Card(suit=Suit.spades, rank=Rank.five)),
            ("4H", Card(suit=Suit.hearts, rank=Rank.four)),
            ("4D", Card(suit=Suit.diamonds, rank=Rank.four)),
            ("4C", Card(suit=Suit.clubs, rank=Rank.four)),
            ("4S", Card(suit=Suit.spades, rank=Rank.four)),
            ("3H", Card(suit=Suit.hearts, rank=Rank.three)),
            ("3D", Card(suit=Suit.diamonds, rank=Rank.three)),
            ("3C", Card(suit=Suit.clubs, rank=Rank.three)),
            ("3S", Card(suit=Suit.spades, rank=Rank.three)),
            ("2H", Card(suit=Suit.hearts, rank=Rank.two)),
            ("2D", Card(suit=Suit.diamonds, rank=Rank.two)),
            ("2C", Card(suit=Suit.clubs, rank=Rank.two)),
            ("2S", Card(suit=Suit.spades, rank=Rank.two)),
        ]
        
        for card_str, expected in test_cases:
            result = string_to_card(card_str)
            assert result.suit == expected.suit, f"Failed suit for {card_str}"
            assert result.rank == expected.rank, f"Failed rank for {card_str}"
    
    def test_string_to_card_invalid_length(self):
        """Test card string with length < 2."""
        invalid_strings = ["", "A", "1", "X"]
        
        for invalid_str in invalid_strings:
            with pytest.raises(ValueError, match=f"Invalid card string format: {invalid_str}"):
                string_to_card(invalid_str)
    
    def test_string_to_card_invalid_rank(self):
        """Test card string with invalid rank."""
        invalid_ranks = ["XS", "1H", "0D", "ZC", "BS"]
        
        for invalid_str in invalid_ranks:
            with pytest.raises(ValueError, match=f"Invalid rank:"):
                string_to_card(invalid_str)
    
    def test_string_to_card_invalid_suit(self):
        """Test card string with invalid suit."""
        invalid_suits = ["AX", "KZ", "QY", "JW", "10X"]
        
        for invalid_str in invalid_suits:
            with pytest.raises(ValueError, match=f"Invalid suit:"):
                string_to_card(invalid_str)
    
    def test_string_to_card_10_edge_cases(self):
        """Test '10' cards with various suits."""
        ten_cards = ["10H", "10D", "10C", "10S"]
        
        for card_str in ten_cards:
            card = string_to_card(card_str)
            assert card.rank == Rank.ten
            assert len(card_str) == 3  # 10 is two characters
    
    def test_string_to_card_10_invalid_format(self):
        """Test invalid 10 card formats."""
        invalid_ten_cards = ["1H", "10", "1", "0H"]
        
        for invalid_str in invalid_ten_cards:
            with pytest.raises(ValueError):
                string_to_card(invalid_str)
    
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
            Card(suit=Suit.diamonds, rank=Rank.nine),
            Card(suit=Suit.clubs, rank=Rank.eight),
        ]
        
        for original_card in test_cards:
            card_str = card_to_string(original_card)
            converted_card = string_to_card(card_str)
            
            assert converted_card.suit == original_card.suit
            assert converted_card.rank == original_card.rank


@pytest.mark.unit
class TestHandConversion:
    """Test hand conversion utilities."""
    
    def test_hand_to_string_empty_hand(self):
        """Test converting empty hand to string."""
        hand = Hand(cards=[])
        hand_str = hand_to_string(hand)
        assert hand_str == '[]'
    
    def test_hand_to_string_single_card(self):
        """Test converting hand with one card."""
        hand = Hand(cards=[Card(suit=Suit.hearts, rank=Rank.ace)])
        hand_str = hand_to_string(hand)
        assert hand_str == '["AH"]'
    
    def test_hand_to_string_multiple_cards(self):
        """Test converting hand with multiple cards."""
        hand = Hand(cards=[
            Card(suit=Suit.spades, rank=Rank.king),
            Card(suit=Suit.hearts, rank=Rank.ace),
            Card(suit=Suit.diamonds, rank=Rank.ten)
        ])
        hand_str = hand_to_string(hand)
        assert hand_str == '["KS", "AH", "10D"]'
    
    def test_hand_to_string_all_cards(self):
        """Test converting hand with all types of cards."""
        hand = Hand(cards=[
            Card(suit=Suit.hearts, rank=Rank.ace),
            Card(suit=Suit.spades, rank=Rank.king),
            Card(suit=Suit.diamonds, rank=Rank.queen),
            Card(suit=Suit.clubs, rank=Rank.jack),
            Card(suit=Suit.hearts, rank=Rank.ten),
            Card(suit=Suit.spades, rank=Rank.nine),
            Card(suit=Suit.diamonds, rank=Rank.eight),
            Card(suit=Suit.clubs, rank=Rank.seven),
            Card(suit=Suit.hearts, rank=Rank.six),
            Card(suit=Suit.spades, rank=Rank.five),
            Card(suit=Suit.diamonds, rank=Rank.four),
            Card(suit=Suit.clubs, rank=Rank.three),
            Card(suit=Suit.hearts, rank=Rank.two)
        ])
        hand_str = hand_to_string(hand)
        expected = '["AH", "KS", "QD", "JC", "10H", "9S", "8D", "7C", "6H", "5S", "4D", "3C", "2H"]'
        assert hand_str == expected
    
    def test_string_to_hand_empty_json_array(self):
        """Test empty JSON array."""
        hand_str = '[]'
        hand = string_to_hand(hand_str)
        assert len(hand.cards) == 0
    
    def test_string_to_hand_single_card(self):
        """Test JSON string with single card."""
        hand_str = '["AH"]'
        hand = string_to_hand(hand_str)
        assert len(hand.cards) == 1
        assert hand.cards[0].suit == Suit.hearts
        assert hand.cards[0].rank == Rank.ace
    
    def test_string_to_hand_multiple_cards(self):
        """Test JSON string with multiple cards."""
        hand_str = '["KS", "AH", "10D"]'
        hand = string_to_hand(hand_str)
        assert len(hand.cards) == 3
        assert hand.cards[0].suit == Suit.spades and hand.cards[0].rank == Rank.king
        assert hand.cards[1].suit == Suit.hearts and hand.cards[1].rank == Rank.ace
        assert hand.cards[2].suit == Suit.diamonds and hand.cards[2].rank == Rank.ten
    
    def test_string_to_hand_invalid_json(self):
        """Test invalid JSON string."""
        invalid_jsons = [
            'invalid json',
            '{"not": "an array"}',
            '["AH", "KS",]',  # Trailing comma
            '["AH", "KS"',   # Missing closing bracket
        ]
        
        for invalid_json in invalid_jsons:
            with pytest.raises(ValueError, match="Invalid hand string format"):
                string_to_hand(invalid_json)
    
    def test_string_to_hand_invalid_card_in_json(self):
        """Test JSON with invalid card string."""
        invalid_hands = [
            '["AH", "invalid"]',
            '["AH", "XS"]',
            '["AH", "KZ"]',
            '["AH", "1H"]',
        ]
        
        for invalid_hand in invalid_hands:
            with pytest.raises(ValueError):
                string_to_hand(invalid_hand)
    
    def test_string_to_hand_malformed_json(self):
        """Test malformed JSON structure."""
        malformed_jsons = [
            '["AH", "KS", "QD",',  # Incomplete
            '["AH", "KS", "QD"',   # Missing closing bracket
            '["AH", "KS", "QD",]', # Trailing comma
            '["AH", "KS", "QD", ""]', # Empty string
        ]
        
        for malformed_json in malformed_jsons:
            with pytest.raises(ValueError):
                string_to_hand(malformed_json)
    
    def test_string_to_hand_json_decode_error(self):
        """Test JSON decode errors."""
        invalid_jsons = [
            '["AH", "KS", "QD",]',  # Trailing comma
            '["AH", "KS", "QD"',    # Missing closing bracket
            '["AH", "KS", "QD",',   # Incomplete
            '["AH", "KS", "QD", ""]', # Empty string in array
        ]
        
        for invalid_json in invalid_jsons:
            with pytest.raises(ValueError, match="Invalid hand string format"):
                string_to_hand(invalid_json)
    
    def test_hand_roundtrip(self):
        """Test hand conversion roundtrip (hand -> string -> hand)."""
        test_hands = [
            Hand(cards=[]),
            Hand(cards=[Card(suit=Suit.hearts, rank=Rank.ace)]),
            Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.king),
                Card(suit=Suit.hearts, rank=Rank.ace)
            ]),
            Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.five),
                Card(suit=Suit.hearts, rank=Rank.queen)
            ]),
        ]
        
        for original_hand in test_hands:
            hand_str = hand_to_string(original_hand)
            converted_hand = string_to_hand(hand_str)
            
            assert len(converted_hand.cards) == len(original_hand.cards)
            for i, card in enumerate(original_hand.cards):
                assert converted_hand.cards[i].suit == card.suit
                assert converted_hand.cards[i].rank == card.rank


@pytest.mark.unit
class TestHandDictionaryConversion:
    """Test hand dictionary conversion utilities."""
    
    def test_hand_to_dict_with_attributes(self):
        """Test converting hand with total, is_soft, etc."""
        hand = Hand(cards=[
            Card(suit=Suit.hearts, rank=Rank.ace),
            Card(suit=Suit.spades, rank=Rank.king)
        ])
        
        hand_dict = hand_to_dict(hand)
        
        assert hand_dict["cards"] == ["AH", "KS"]
        # Hand model doesn't have these attributes by default, so they should be None
        assert hand_dict["total"] is None
        assert hand_dict["is_soft"] is None
        assert hand_dict["is_bust"] is None
        assert hand_dict["is_blackjack"] is None
    
    def test_hand_to_dict_without_attributes(self):
        """Test converting hand without optional attributes."""
        hand = Hand(cards=[
            Card(suit=Suit.diamonds, rank=Rank.ten),
            Card(suit=Suit.clubs, rank=Rank.five)
        ])
        
        hand_dict = hand_to_dict(hand)
        
        assert hand_dict["cards"] == ["10D", "5C"]
        # Optional attributes should be None since Hand model doesn't have them
        assert hand_dict["total"] is None
        assert hand_dict["is_soft"] is None
        assert hand_dict["is_bust"] is None
        assert hand_dict["is_blackjack"] is None
    
    def test_hand_to_dict_empty_hand(self):
        """Test converting empty hand to dict."""
        hand = Hand(cards=[])
        hand_dict = hand_to_dict(hand)
        
        assert hand_dict["cards"] == []
    
    def test_hand_to_dict_single_card(self):
        """Test converting hand with single card to dict."""
        hand = Hand(cards=[Card(suit=Suit.hearts, rank=Rank.ace)])
        hand_dict = hand_to_dict(hand)
        
        assert hand_dict["cards"] == ["AH"]
    
    def test_dict_to_hand_empty_cards(self):
        """Test converting dict with empty cards list."""
        hand_dict = {"cards": []}
        hand = dict_to_hand(hand_dict)
        
        assert len(hand.cards) == 0
    
    def test_dict_to_hand_single_card(self):
        """Test converting dict with single card."""
        hand_dict = {"cards": ["AH"]}
        hand = dict_to_hand(hand_dict)
        
        assert len(hand.cards) == 1
        assert hand.cards[0].suit == Suit.hearts
        assert hand.cards[0].rank == Rank.ace
    
    def test_dict_to_hand_multiple_cards(self):
        """Test converting dict with multiple cards."""
        hand_dict = {"cards": ["KS", "AH", "10D"]}
        hand = dict_to_hand(hand_dict)
        
        assert len(hand.cards) == 3
        assert hand.cards[0].suit == Suit.spades and hand.cards[0].rank == Rank.king
        assert hand.cards[1].suit == Suit.hearts and hand.cards[1].rank == Rank.ace
        assert hand.cards[2].suit == Suit.diamonds and hand.cards[2].rank == Rank.ten
    
    def test_dict_to_hand_missing_cards_key(self):
        """Test converting dict without cards key."""
        hand_dict = {"total": 21, "is_soft": False}
        
        # Should create empty hand when cards key is missing
        hand = dict_to_hand(hand_dict)
        assert len(hand.cards) == 0
    
    def test_dict_to_hand_invalid_card_string(self):
        """Test converting dict with invalid card string."""
        hand_dict = {"cards": ["AH", "invalid"]}
        
        with pytest.raises(ValueError):
            dict_to_hand(hand_dict)
    
    def test_dict_to_hand_none_cards(self):
        """Test converting dict with None cards."""
        hand_dict = {"cards": None}
        
        # Should handle None gracefully
        hand = dict_to_hand(hand_dict)
        assert len(hand.cards) == 0
    
    def test_dict_to_hand_empty_dict(self):
        """Test converting empty dict."""
        hand_dict = {}
        
        # Should create empty hand
        hand = dict_to_hand(hand_dict)
        assert len(hand.cards) == 0
    
    def test_dict_to_hand_roundtrip(self):
        """Test hand dict conversion roundtrip (hand -> dict -> hand)."""
        test_hands = [
            Hand(cards=[]),
            Hand(cards=[Card(suit=Suit.hearts, rank=Rank.ace)]),
            Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.king),
                Card(suit=Suit.hearts, rank=Rank.ace)
            ]),
            Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.five),
                Card(suit=Suit.hearts, rank=Rank.queen)
            ]),
        ]
        
        for original_hand in test_hands:
            hand_dict = hand_to_dict(original_hand)
            converted_hand = dict_to_hand(hand_dict)
            
            assert len(converted_hand.cards) == len(original_hand.cards)
            for i, card in enumerate(original_hand.cards):
                assert converted_hand.cards[i].suit == card.suit
                assert converted_hand.cards[i].rank == card.rank 