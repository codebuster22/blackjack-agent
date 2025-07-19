import pytest
from dealer_agent.tools.dealer import placeBet, GameState, shuffleShoe


class TestPlaceBet:
    """Test cases for placeBet() function."""
    
    def test_normal_bet_deduction(self):
        """
        Test normal bet deduction from chips.
        Expected result: Chips reduced by bet amount, bet set to amount.
        Mock values: GameState with chips=100, bet amount=30.
        Why: Verify basic bet placement functionality works correctly.
        """
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        
        state = placeBet(state, 30.0)
        
        assert state.chips == 70.0
        assert state.bet == 30.0
    
    def test_zero_bet_raises_error(self):
        """
        Test that zero bet raises ValueError.
        Expected result: ValueError with message "Bet amount must be positive."
        Mock values: GameState with chips=100, bet amount=0.
        Why: Ensure invalid bet amounts are rejected.
        """
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        original_chips = state.chips
        original_bet = state.bet
        
        with pytest.raises(ValueError, match="Bet amount must be positive."):
            placeBet(state, 0.0)
        
        # Verify no changes to state
        assert state.chips == original_chips
        assert state.bet == original_bet
    
    def test_negative_bet_raises_error(self):
        """
        Test that negative bet raises ValueError.
        Expected result: ValueError with message "Bet amount must be positive."
        Mock values: GameState with chips=100, bet amount=-10.
        Why: Ensure negative bet amounts are rejected.
        """
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        original_chips = state.chips
        original_bet = state.bet
        
        with pytest.raises(ValueError, match="Bet amount must be positive."):
            placeBet(state, -10.0)
        
        # Verify no changes to state
        assert state.chips == original_chips
        assert state.bet == original_bet
    
    def test_insufficient_chips_raises_error(self):
        """
        Test that insufficient chips raises ValueError.
        Expected result: ValueError with message "Insufficient chips to place bet."
        Mock values: GameState with chips=20, bet amount=50.
        Why: Ensure bets cannot exceed available chips.
        """
        state = GameState(shoe=shuffleShoe(), chips=20.0)
        original_chips = state.chips
        original_bet = state.bet
        
        with pytest.raises(ValueError, match="Insufficient chips to place bet."):
            placeBet(state, 50.0)
        
        # Verify no changes to state
        assert state.chips == original_chips
        assert state.bet == original_bet
    
    def test_exact_chips_bet_succeeds(self):
        """
        Test that betting exactly available chips succeeds.
        Expected result: Chips reduced to 0, bet set to amount.
        Mock values: GameState with chips=25, bet amount=25.
        Why: Verify edge case where bet equals available chips.
        """
        state = GameState(shoe=shuffleShoe(), chips=25.0)
        
        state = placeBet(state, 25.0)
        
        assert state.chips == 0.0
        assert state.bet == 25.0 