import pytest
from dealer_agent.tools.dealer import processPlayerAction


class TestProcessPlayerActionSimple:
    """Test processPlayerAction function simple error cases."""
    
    def test_process_player_action_invalid_action(self):
        """Test processPlayerAction with invalid action."""
        result = processPlayerAction("invalid_action")
        assert result["success"] is False
        assert "Action must be 'hit' or 'stand'" in result["error"]
    
    def test_process_player_action_invalid_action_uppercase(self):
        """Test processPlayerAction with invalid action in uppercase."""
        result = processPlayerAction("INVALID")
        assert result["success"] is False
        assert "Action must be 'hit' or 'stand'" in result["error"]
    
    def test_process_player_action_empty_string(self):
        """Test processPlayerAction with empty string."""
        result = processPlayerAction("")
        assert result["success"] is False
        assert "Action must be 'hit' or 'stand'" in result["error"] 