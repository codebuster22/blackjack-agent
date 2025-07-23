import pytest
from unittest.mock import Mock
from dealer_agent.tools.dealer import initialize_game


class TestInitializeGame:
    """Test initialize_game function error handling."""
    
    def test_initialize_game_with_tool_context_but_missing_session_id(self):
        """Test initialize_game when tool_context provided but session_id is missing."""
        tool_context = Mock()
        tool_context.state = {}  # No session_id or user_id
        
        result = initialize_game(tool_context=tool_context)
        # This should succeed since session_id is not required for initialization
        assert result["success"] is True
    
    def test_initialize_game_with_tool_context_but_missing_user_id(self):
        """Test initialize_game when tool_context provided but user_id is missing."""
        tool_context = Mock()
        tool_context.state = {"session_id": "test_session_123"}  # No user_id
        
        result = initialize_game(tool_context=tool_context)
        # This should succeed since user_id is not required for initialization
        assert result["success"] is True
    
    def test_initialize_game_with_tool_context_but_missing_both_ids(self):
        """Test initialize_game when tool_context provided but both session_id and user_id are missing."""
        tool_context = Mock()
        tool_context.state = {}  # No session_id or user_id
        
        result = initialize_game(tool_context=tool_context)
        # This should succeed since neither is required for initialization
        assert result["success"] is True 