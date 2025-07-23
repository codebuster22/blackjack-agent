import pytest
from dealer_agent.tools.dealer import updateChips, GameState, shuffleShoe, set_current_state


class TestUpdateChips:
    """Test cases for updateChips() function."""
    
    def test_positive_payout_win(self):
        """
        Test positive payout (win) increases chips.
        Expected result: Chips increased by payout amount.
        Mock values: GameState with chips=70, payout=30.
        Why: Verify winning payouts correctly increase chip balance.
        """
        state = GameState(shoe=shuffleShoe(), chips=70.0)
        set_current_state(state)
        
        result = updateChips(30.0)
        
        assert result["success"] is True
        assert result["chips"] == 100.0
    
    def test_negative_payout_loss(self):
        """
        Test negative payout (loss) decreases chips.
        Expected result: Chips decreased by absolute value of payout.
        Mock values: GameState with chips=100, payout=-25.
        Why: Verify losing payouts correctly decrease chip balance.
        """
        state = GameState(shoe=shuffleShoe(), chips=100.0)
        set_current_state(state)
        
        result = updateChips(-25.0)
        
        assert result["success"] is True
        assert result["chips"] == 75.0
    
    def test_zero_payout_push(self):
        """
        Test zero payout (push) leaves chips unchanged.
        Expected result: Chips remain the same.
        Mock values: GameState with chips=55, payout=0.
        Why: Verify push payouts don't change chip balance.
        """
        state = GameState(shoe=shuffleShoe(), chips=55.0)
        set_current_state(state)
        
        result = updateChips(0.0)
        
        assert result["success"] is True
        assert result["chips"] == 55.0
    
    def test_large_positive_payout(self):
        """
        Test large positive payout works correctly.
        Expected result: Chips increased by large amount.
        Mock values: GameState with chips=10, payout=1000.
        Why: Verify large payouts are handled correctly.
        """
        state = GameState(shoe=shuffleShoe(), chips=10.0)
        set_current_state(state)
        
        result = updateChips(1000.0)
        
        assert result["success"] is True
        assert result["chips"] == 1010.0
    
    def test_large_negative_payout(self):
        """
        Test large negative payout works correctly.
        Expected result: Chips decreased by large amount.
        Mock values: GameState with chips=1000, payout=-500.
        Why: Verify large losses are handled correctly.
        """
        state = GameState(shoe=shuffleShoe(), chips=1000.0)
        set_current_state(state)
        
        result = updateChips(-500.0)
        
        assert result["success"] is True
        assert result["chips"] == 500.0
    
    def test_fractional_payout(self):
        """
        Test fractional payout works correctly.
        Expected result: Chips updated with fractional precision.
        Mock values: GameState with chips=100.5, payout=25.75.
        Why: Verify fractional payouts are handled with proper precision.
        """
        state = GameState(shoe=shuffleShoe(), chips=100.5)
        set_current_state(state)
        
        result = updateChips(25.75)
        
        assert result["success"] is True
        assert result["chips"] == 126.25 