# Cursed decorator to vibe Python on the fly

Are you tired of asking an LLM for some code and then having to **wait** to run it? I know I am. But now we can do better! With this cursed decorator you can vibe Python on the fly! Just define an empty function with a descriptive name and decorate it with `@ai_implement`, and OpenAI will implement during runtime!

**Before:**

> Please Mr. GPT, implement for me a Python function called `check_if_number_is_prime`. 🥺

**After:**

```python
from cursed_vibing_on_the_fly import ai_implement

@ai_implement
def check_if_number_is_prime(n):
    pass
```

The system can even include docstrings or pydantic type annotations if you want that fine extra control!

```python
from typing import Union
from cursed_vibing_on_the_fly import ai_implement

@ai_implement
def round_float(number):
    """Rounds a given float to the nearest integer."""
    pass


@ai_implement
def check_if_string_equals_number(string_input: str, comparison_number: Union[float, int]) -> bool:
    """
    This function tries to parse a string into a float or int and then see if the value equals `comparison_number`.
    """
    pass
```

## Quickstart

Don't. Quickly or at all. **This really does run `exec` on raw LLM output on your machine.** But if you must:

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- `OPENAI_API_KEY` environment variable set.

### Installation & Usage

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd cursed_vibing_on_the_fly
   ```

2. Sync dependencies:

   ```bash
   uv sync
   ```

3. Run the demo:

   ```bash
   uv run examples/demo.py
   ```

4. Run tests:

   ```bash
   # Run safe tests (mocked)
   uv run pytest

   # Run dangerous tests (real API calls)
   uv run pytest -m dangerous
   ```
