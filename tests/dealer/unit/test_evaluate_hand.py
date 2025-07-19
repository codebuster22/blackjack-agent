import pytest
from dealer_agent.tools.dealer import evaluateHand, Hand, Card, Suit, Rank


class TestEvaluateHand:
    """Test cases for evaluateHand() function."""
    
    def test_simple_totals(self):
        """
        Test hand evaluation with simple number cards.
        Expected result: Total 11, is_soft=False, is_blackjack=False, is_bust=False.
        Mock values: Hand with [2♣, 9♦].
        Why: Verify basic addition of number cards works correctly.
        """
        hand = Hand(cards=[
            Card(suit=Suit.clubs, rank=Rank.two),
            Card(suit=Suit.diamonds, rank=Rank.nine)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 11
        assert result.is_soft is False
        assert result.is_blackjack is False
        assert result.is_bust is False
    
    def test_face_cards(self):
        """
        Test hand evaluation with face cards (K, Q, J).
        Expected result: Total 20, is_soft=False, is_blackjack=False, is_bust=False.
        Mock values: Hand with [K♠, Q♥].
        Why: Verify face cards are correctly valued at 10 points each.
        """
        hand = Hand(cards=[
            Card(suit=Suit.spades, rank=Rank.king),
            Card(suit=Suit.hearts, rank=Rank.queen)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 20
        assert result.is_soft is False
        assert result.is_blackjack is False
        assert result.is_bust is False
    
    def test_single_ace(self):
        """
        Test hand evaluation with a single ace that can be counted as 11.
        Expected result: Total 16 (11+5), is_soft=True, is_blackjack=False, is_bust=False.
        Mock values: Hand with [A♣, 5♦].
        Why: Verify ace is correctly counted as 11 when beneficial.
        """
        hand = Hand(cards=[
            Card(suit=Suit.clubs, rank=Rank.ace),
            Card(suit=Suit.diamonds, rank=Rank.five)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 16
        assert result.is_soft is True
        assert result.is_blackjack is False
        assert result.is_bust is False
    
    def test_multiple_aces(self):
        """
        Test hand evaluation with multiple aces.
        Expected result: Total 20, is_soft=True (one ace as 11, one as 1).
        Mock values: Hand with [A♠, A♥, 8♣].
        Why: Verify multiple aces are handled correctly with optimal counting.
        """
        hand = Hand(cards=[
            Card(suit=Suit.spades, rank=Rank.ace),
            Card(suit=Suit.hearts, rank=Rank.ace),
            Card(suit=Suit.clubs, rank=Rank.eight)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 20
        assert result.is_soft is True
        assert result.is_blackjack is False
        assert result.is_bust is False
    
    def test_blackjack_detection(self):
        """
        Test blackjack detection with ace and face card.
        Expected result: Total 21, is_blackjack=True.
        Mock values: Hand with [A♦, K♣].
        Why: Verify blackjack is correctly identified when total is 21 with exactly 2 cards.
        """
        hand = Hand(cards=[
            Card(suit=Suit.diamonds, rank=Rank.ace),
            Card(suit=Suit.clubs, rank=Rank.king)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 21
        assert result.is_soft is True
        assert result.is_blackjack is True
        assert result.is_bust is False
    
    def test_bust(self):
        """
        Test bust detection when hand total exceeds 21.
        Expected result: Total 24, is_bust=True.
        Mock values: Hand with [10♠, 9♦, 5♥].
        Why: Verify bust is correctly identified when total exceeds 21.
        """
        hand = Hand(cards=[
            Card(suit=Suit.spades, rank=Rank.ten),
            Card(suit=Suit.diamonds, rank=Rank.nine),
            Card(suit=Suit.hearts, rank=Rank.five)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 24
        assert result.is_soft is False
        assert result.is_blackjack is False
        assert result.is_bust is True
    
    def test_ace_as_one_when_bust_risk(self):
        """
        Test that ace is counted as 1 when counting as 11 would cause bust.
        Expected result: Total 13, is_soft=False.
        Mock values: Hand with [A♣, 10♦, 2♥].
        Why: Verify ace is correctly counted as 1 to avoid bust.
        """
        hand = Hand(cards=[
            Card(suit=Suit.clubs, rank=Rank.ace),
            Card(suit=Suit.diamonds, rank=Rank.ten),
            Card(suit=Suit.hearts, rank=Rank.two)
        ])
        
        result = evaluateHand(hand)
        
        assert result.total == 13
        assert result.is_soft is False
        assert result.is_blackjack is False
        assert result.is_bust is False 