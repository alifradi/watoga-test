import pytest
import uuid
from unittest.mock import Mock, patch
from app.service import create_feature, get_feature

def test_create_feature_returns_uuid():
    """Test that create_feature returns a valid UUID."""
    # Mock database session
    mock_db = Mock()
    mock_db.execute.return_value = None
    mock_db.commit.return_value = None
    
    # Call the function
    result = create_feature(mock_db, "Test Feature", 45.5017, -73.5673)
    
    # Verify result is a UUID
    assert isinstance(result, uuid.UUID)
    
    # Verify database was called
    assert mock_db.execute.called
    assert mock_db.commit.called

def test_get_feature_returns_none_for_nonexistent():
    """Test that get_feature returns None for non-existent feature."""
    # Mock database session with no results
    mock_db = Mock()
    mock_result = Mock()
    mock_result.fetchone.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Call the function
    result = get_feature(mock_db, "non-existent-id")
    
    # Verify result is None
    assert result is None
    
    # Verify database was queried
    assert mock_db.execute.called

