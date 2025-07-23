import pytest
from unittest.mock import Mock
from dealer_agent.tools.dealer import get_current_session_state, get_current_user_id


class TestToolContext:
    """Test tool context utility functions."""
    
    def test_get_current_session_state_with_session_id(self):
        """Test getting session state when session_id exists."""
        tool_context = Mock()
        tool_context.state = {"session_id": "test_session_123"}
        
        session_state = get_current_session_state(tool_context)
        assert session_state == "test_session_123"
    
    def test_get_current_session_state_missing_session_id(self):
        """Test getting session state when session_id is missing."""
        tool_context = Mock()
        tool_context.state = {"user_id": "test_user_456"}  # No session_id
        
        session_state = get_current_session_state(tool_context)
        assert session_state is None
    
    def test_get_current_user_id_with_user_id(self):
        """Test getting user ID when user_id exists."""
        tool_context = Mock()
        tool_context.state = {"user_id": "test_user_456"}
        
        user_id = get_current_user_id(tool_context)
        assert user_id == "test_user_456"
    
    def test_get_current_user_id_missing_user_id(self):
        """Test getting user ID when user_id is missing."""
        tool_context = Mock()
        tool_context.state = {"session_id": "test_session_123"}  # No user_id
        
        user_id = get_current_user_id(tool_context)
        assert user_id is None 