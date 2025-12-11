import pytest
import os
from cursed_vibing_on_the_fly import ai_implement

@pytest.mark.dangerous
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_dangerous_is_odd():
    @ai_implement
    def is_odd(n: int) -> bool:
        """Check if number is odd."""
        pass

    assert is_odd(3) is True
    assert is_odd(4) is False

