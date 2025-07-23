import pytest
from dealer_agent.tools.dealer import displayState, GameState, Hand, Card, Suit, Rank, shuffleShoe, updateChips, set_current_state


class TestDisplayState:
    """Test cases for displayState() function."""
    
    def test_hide_dealer_hole(self):
        """
        Test display when dealer hole card is hidden.
        Expected result: Player hand with total, dealer up-card only.
        Mock values: Known hands, revealDealerHole=False.
        Why: Verify correct display format during player's turn.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.king)
            ])
        )
        set_current_state(state)
        
        result = displayState(revealDealerHole=False)
        
        # Check success
        assert result["success"] == True
        # Check player hand displayed with total and chips
        assert "Player Hand: ['Rank.tenSuit.hearts', 'Rank.fiveSuit.diamonds'] (Total: 15)" in result["display_text"]
        assert "Chips: 100.0" in result["display_text"]
        # Check only dealer up-card shown
        assert "Dealer Up-Card: Rank.aceSuit.spades" in result["display_text"]
        # Check dealer hole card not shown
        assert "Dealer Hand:" not in result["display_text"]
    
    def test_reveal_dealer_hole(self):
        """
        Test display when dealer hole card is revealed.
        Expected result: Both hands with totals displayed.
        Mock values: Known hands, revealDealerHole=True.
        Why: Verify correct display format when showing final results.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ten),
                Card(suit=Suit.diamonds, rank=Rank.five)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.spades, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.king)
            ])
        )
        set_current_state(state)
        
        result = displayState(revealDealerHole=True)
        
        # Check success
        assert result["success"] == True
        # Check player hand displayed with total and chips
        assert "Player Hand: ['Rank.tenSuit.hearts', 'Rank.fiveSuit.diamonds'] (Total: 15)" in result["display_text"]
        assert "Chips: 100.0" in result["display_text"]
        # Check dealer hand displayed with total
        assert "Dealer Hand: ['Rank.aceSuit.spades', 'Rank.kingSuit.clubs'] (Total: 21)" in result["display_text"]
        # Check dealer up-card not shown separately
        assert "Dealer Up-Card:" not in result["display_text"]
    
    def test_empty_hands(self):
        """
        Test display with empty hands.
        Expected result: Empty hands displayed with total 0.
        Mock values: Empty hands.
        Why: Verify graceful handling of empty hands.
        """
        state = GameState(
            shoe=shuffleShoe(),
            player_hand=Hand(cards=[]),
            dealer_hand=Hand(cards=[])
        )
        set_current_state(state)
        
        result = displayState(revealDealerHole=True)
        
        # Check success
        assert result["success"] == True
        # Check empty hands displayed with chips
        assert "Player Hand: [] (Total: 0)" in result["display_text"]
        assert "Dealer Hand: No cards yet" in result["display_text"]
        assert "Chips: 100.0" in result["display_text"]
    
    def test_hide_dealer_hole_with_specific_cards(self):
        """
        Test display when dealer hole card is hidden with specific known cards.
        Expected result: Player hand with total and chips, dealer up-card only.
        Mock values: Player cards [A♥, 9♣], dealer cards [K♦, 5♠], chips=80.
        Why: Verify display format with specific card combinations.
        """
        state = GameState(
            shoe=shuffleShoe(),
            chips=80.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.nine)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ])
        )
        set_current_state(state)
        
        result = displayState(revealDealerHole=False)
        
        # Check success
        assert result["success"] == True
        # Check player hand displayed with total and chips
        assert "Player Hand: ['Rank.aceSuit.hearts', 'Rank.nineSuit.clubs'] (Total: 20)" in result["display_text"]
        assert "Chips: 80.0" in result["display_text"]
        # Check only dealer up-card shown
        assert "Dealer Up-Card: Rank.kingSuit.diamonds" in result["display_text"]
        # Check dealer hole card not shown
        assert "Dealer Hand:" not in result["display_text"]
    
    def test_reveal_dealer_hole_with_specific_cards(self):
        """
        Test display when dealer hole card is revealed with specific known cards.
        Expected result: Both hands with totals displayed.
        Mock values: Player cards [A♥, 9♣], dealer cards [K♦, 5♠], chips=80.
        Why: Verify display format with specific card combinations when revealing dealer.
        """
        state = GameState(
            shoe=shuffleShoe(),
            chips=80.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.nine)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ])
        )
        set_current_state(state)
        
        result = displayState(revealDealerHole=True)
        
        # Check success
        assert result["success"] == True
        # Check player hand displayed with total and chips
        assert "Player Hand: ['Rank.aceSuit.hearts', 'Rank.nineSuit.clubs'] (Total: 20)" in result["display_text"]
        assert "Chips: 80.0" in result["display_text"]
        # Check dealer hand displayed with total
        assert "Dealer Hand: ['Rank.kingSuit.diamonds', 'Rank.fiveSuit.spades'] (Total: 15)" in result["display_text"]
        # Check dealer up-card not shown separately
        assert "Dealer Up-Card:" not in result["display_text"]
    
    def test_after_payout_reflection(self):
        """
        Test display after payout reflection shows updated chips.
        Expected result: Player hand with total and updated chips after win.
        Mock values: After win, chips updated from 80 to 100.
        Why: Verify chips display updates correctly after payouts.
        """
        state = GameState(
            shoe=shuffleShoe(),
            chips=80.0,
            player_hand=Hand(cards=[
                Card(suit=Suit.hearts, rank=Rank.ace),
                Card(suit=Suit.clubs, rank=Rank.nine)
            ]),
            dealer_hand=Hand(cards=[
                Card(suit=Suit.diamonds, rank=Rank.king),
                Card(suit=Suit.spades, rank=Rank.five)
            ])
        )
        set_current_state(state)
        
        # Simulate winning payout
        updateChips(20.0)
        
        result = displayState(revealDealerHole=False)
        
        # Check success
        assert result["success"] == True
        # Check player hand displayed with total and updated chips
        assert "Player Hand: ['Rank.aceSuit.hearts', 'Rank.nineSuit.clubs'] (Total: 20)" in result["display_text"]
        assert "Chips: 100.0" in result["display_text"]
        # Check only dealer up-card shown
        assert "Dealer Up-Card: Rank.kingSuit.diamonds" in result["display_text"]
    
    def test_edge_case_empty_hands_before_deal(self):
        """
        Test display with empty hands before any deal.
        Expected result: Player hand shows empty list and total 0, dealer up-card may error.
        Mock values: New GameState before any deal, chips=100.
        Why: Verify graceful handling of empty hands before dealing.
        """
        state = GameState(
            shoe=shuffleShoe(),
            chips=100.0,
            player_hand=Hand(cards=[]),
            dealer_hand=Hand(cards=[])
        )
        set_current_state(state)
        
        # This should handle empty hands gracefully now
        result = displayState(revealDealerHole=False)
        
        # Check success
        assert result["success"] == True
        # Check empty hands displayed with chips
        assert "Player Hand: [] (Total: 0)" in result["display_text"]
        assert "Chips: 100.0" in result["display_text"]
        assert "Dealer Hand: No cards yet" in result["display_text"] 