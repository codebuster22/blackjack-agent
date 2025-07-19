import pytest
from dealer_agent.tools.dealer import settleBet, GameState, Hand, Card, Suit, Rank, shuffleShoe


class TestSettleBet:
    """Test cases for settleBet() function."""
    
    def test_player_bust(self):
        """
        Test settlement when player busts.
        Expected result: Payout = -bet, result = 'loss'.
        Mock values: Player hand bust (24), dealer hand valid (18), bet = 100.
        Why: Verify player loses when they bust regardless of dealer's hand.
        """
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
        
        payout, result = settleBet(state)
        
        assert payout == -100.0
        assert result == 'loss'
    
    def test_dealer_bust(self):
        """
        Test settlement when dealer busts but player doesn't.
        Expected result: Payout = +bet, result = 'win'.
        Mock values: Player hand valid (18), dealer hand bust (23), bet = 50.
        Why: Verify player wins when dealer busts and player doesn't.
        """
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
        
        payout, result = settleBet(state)
        
        assert payout == 50.0
        assert result == 'win'
    
    def test_player_blackjack(self):
        """
        Test settlement when player has blackjack and dealer doesn't.
        Expected result: Payout = +1.5×bet, result = 'win'.
        Mock values: Player blackjack (A+K), dealer not blackjack (10+7), bet = 100.
        Why: Verify blackjack pays 3:2 (1.5× bet).
        """
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
        
        payout, result = settleBet(state)
        
        assert payout == 150.0  # 1.5 × 100
        assert result == 'win'
    
    def test_dealer_blackjack(self):
        """
        Test settlement when dealer has blackjack and player doesn't.
        Expected result: Payout = -bet, result = 'loss'.
        Mock values: Dealer blackjack (A+Q), player not blackjack (10+8), bet = 75.
        Why: Verify player loses when dealer has blackjack and they don't.
        """
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
        
        payout, result = settleBet(state)
        
        assert payout == -75.0
        assert result == 'loss'
    
    def test_mutual_blackjack_push(self):
        """
        Test settlement when both player and dealer have blackjack.
        Expected result: Payout = 0, result = 'push'.
        Mock values: Both hands are blackjack (A+K), bet = 200.
        Why: Verify push when both have blackjack.
        """
        state = GameState(
            shoe=shuffleShoe(),
            bet=200.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.diamonds, rank=Rank.king)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.king)
            ])
        )
        
        payout, result = settleBet(state)
        
        assert payout == 0.0
        assert result == 'push'
    
    def test_higher_total_wins(self):
        """
        Test settlement when neither bust nor blackjack, higher total wins.
        Expected result: Player 19 vs Dealer 17 → +bet.
        Mock values: Player total 19, dealer total 17, bet = 60.
        Why: Verify standard comparison when neither special condition applies.
        """
        state = GameState(
            shoe=shuffleShoe(),
            bet=60.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.nine)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.seven)
            ])
        )
        
        payout, result = settleBet(state)
        
        assert payout == 60.0
        assert result == 'win'
    
    def test_lower_total_loses(self):
        """
        Test settlement when player has lower total than dealer.
        Expected result: Player 16 vs Dealer 18 → -bet.
        Mock values: Player total 16, dealer total 18, bet = 40.
        Why: Verify player loses when they have lower total.
        """
        state = GameState(
            shoe=shuffleShoe(),
            bet=40.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.six)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.eight)
            ])
        )
        
        payout, result = settleBet(state)
        
        assert payout == -40.0
        assert result == 'loss'
    
    def test_equal_total_push(self):
        """
        Test settlement when player and dealer have equal totals.
        Expected result: Player 18 vs Dealer 18 → 0.
        Mock values: Both totals 18, bet = 80.
        Why: Verify push when totals are equal.
        """
        state = GameState(
            shoe=shuffleShoe(),
            bet=80.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.eight)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ten),
                Card(suit=Suit.clubs, rank=Rank.eight)
            ])
        )
        
        payout, result = settleBet(state)
        
        assert payout == 0.0
        assert result == 'push' 