import pytest
from unittest.mock import MagicMock, patch
from cursed_vibing_on_the_fly.core import ai_implement

@pytest.fixture
def mock_openai():
    mock_client = MagicMock()
    # Patch _get_client to return our mock client
    with patch("cursed_vibing_on_the_fly.core._get_client", return_value=mock_client):
        yield mock_client

def test_ai_implement_success(mock_openai):
    # Setup mock to return valid python code
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "return a + b"
    mock_openai.chat.completions.create.return_value = mock_response

    @ai_implement
    def add(a: int, b: int) -> int:
        pass

    assert add(1, 2) == 3
    mock_openai.chat.completions.create.assert_called_once()

def test_ai_implement_syntax_error_retry(mock_openai):
    # Setup mock to return invalid code first, then valid code
    bad_response = MagicMock()
    bad_response.choices[0].message.content = "return a +"  # Syntax error

    good_response = MagicMock()
    good_response.choices[0].message.content = "return a + b"

    mock_openai.chat.completions.create.side_effect = [bad_response, good_response]

    @ai_implement
    def add_retry(a: int, b: int) -> int:
        pass

    assert add_retry(1, 2) == 3
    assert mock_openai.chat.completions.create.call_count == 2
