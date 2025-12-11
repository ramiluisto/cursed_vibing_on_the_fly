# Cursed decorator to vibe Python on the fly

Are you tired of asking an LLM for some code and then having to **wait** to run it? I know I am. But now we can do better! With this cursed decorator you can vibe Python on the fly! Just define an empty function with a descriptive name and decorate it with `@ai_implement`, and OpenAI will implement it during runtime!

**Before:**

> Please Mr. GPT, implement for me a Python function called `check_if_number_is_prime`. 🥺

**After:**

```python
from cursed_vibing_on_the_fly import ai_implement

@ai_implement
def check_if_number_is_prime(n):
    pass
```

After this, any time you use the `check_if_number_is_prime` function, the decorator will automatically ask `gpt-5-mini` to implement a function of this name and then run it on the fly.

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

For a mockery of replicability, the system can be set to cache the LLM-invocations for function persistency between calls (in-memory only, lost on restart). As boring as that is.

## Quickstart

Don't. Quickly or at all. **This really does run `exec` on raw LLM output on your machine.** But if you must:

### Prerequisites

* [uv](https://github.com/astral-sh/uv) installed.
* `OPENAI_API_KEY` environment variable set.

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

### Configuration

You can control behavior with environment variables:

* `OPENAI_API_KEY`: Required for API access.
* `CURSED_VIBING_CACHE_ENABLED`: Set to `true` to enable caching (default: `false`). When disabled, the LLM is called on **every function execution**.
* `AI_IMPLEMENT_RETRY_LIMIT`: Number of retries on generation failure (default: 3).

### Pro mode

Suppose you have a project with an imaginatively named `main.py` as the entrypoint at the project root folder. Then you could save the following little snippet of code in the same folder as `main.py` with the name `run.py`. This new `run.py` then should work identically to `main.py`, except that **every**. **single**. **Python**, **function**. **used**. is automatically decorated with the placeholder `my_dec` decorator.

I'm not giving you the version where we have `ai_implement` in place of `my_dec` because frankly I'm too scared that one of you would actually run it. If you want to, it's not hard to implement and perhaps that small delay will afford you the time to reconsider. 

Note that the cursed `ai_im plement` decorator does not check if the function is actually implemented but always calls an LLM to implement it. We note that having a single `argparse` CLI argument in `main.py` will produce 124 invocations of `my_dec`. I doubt any non-trivial project would survive "pro-mode".


```python
"""
This run.py file is supposed to be placed in the root of a project
where a main.py functions as the main entrypoint. Calling
`python run.py` will then work similarly to `python main.py`,
except that *every* Python function will be decorated with the
`my_dec` decorator below.

This is **NOT** a Pythonic thing to do.
This is **NOT** a sane thing to do.
This is a fun thing to do.
It's cool that it is possible.
"""

import sys
import ast
from importlib.machinery import ModuleSpec
from importlib.abc import MetaPathFinder, Loader
from importlib.util import decode_source
from pathlib import Path

_FORBIDDEN = frozenset(sys.modules.keys())


def my_dec(fn):
    def wrapper(*args, **kwargs):
        print(
            f"\t🫣🫣🫣 [decorator injection at] {fn.__module__}.{fn.__name__}() 🫣🫣🫣"
        )
        return fn(*args, **kwargs)

    return wrapper


class Injector(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.decorator_list.insert(0, ast.Name(id="__auto_dec__", ctx=ast.Load()))
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


class LoaderX(Loader):
    def __init__(self, origin):
        self._origin = origin

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        source = decode_source(Path(self._origin).read_bytes())
        tree = Injector().visit(ast.parse(source))
        ast.fix_missing_locations(tree)
        module.__dict__["__auto_dec__"] = my_dec
        exec(compile(tree, self._origin, "exec"), module.__dict__)


class FinderX(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in _FORBIDDEN:
            return None
        for finder in sys.meta_path:
            if finder is self:
                continue
            spec = getattr(finder, "find_spec", lambda *a: None)(fullname, path, target)
            if spec and spec.origin and spec.origin.endswith(".py"):
                return ModuleSpec(
                    fullname,
                    LoaderX(spec.origin),
                    origin=spec.origin,
                    is_package=spec.submodule_search_locations is not None,
                )
        return None


sys.meta_path.insert(0, FinderX())

# The following bit is here to make this work as a drop-in replacement
# entry point for main.py. If we would just `import main` here, then the classical
# `if __name__ == "__main__":` trigger would not work as the `__name__` that
# an *imported* main.py would see would just be "main". So this trick here
# runs main.py in such a way that main.py sees `__name__` as "__main__".
#
_main_path = Path(__file__).parent / "main.py"
sys.argv[0] = str(_main_path)  # Fix argv so main.py sees itself as the script
_source = decode_source(_main_path.read_bytes())
_tree = Injector().visit(ast.parse(_source))
ast.fix_missing_locations(_tree)
exec(
    compile(_tree, str(_main_path), "exec"),
    {
        "__name__": "__main__",
        "__file__": str(_main_path),
        "__auto_dec__": my_dec,
    },
)
```

## How it all works

When you decorate a function with `@ai_implement`, the following happens:

1. **Inspection**: The decorator inspects your function stub. It gathers:
    * The function name.
    * The docstring (if provided).
    * Type hints (including Pydantic models and `Annotated` descriptions).
    * Parameter names and default values.

2. **Generation & Execution**:
    * The metadata is compiled into a system prompt that asks an LLM (GPT-5-mini by default) to implement the function body.
    * The actual request to the LLM is **NOT** made when you import the module or define the function. It happens only **when you call the function**. This keeps the code feel much more alive and vibrant.
    * The LLM (hopefully) returns Python code. 
    * The code is cleaned (markdown stripped).
    * **DANGER**: The code is executed using `exec()` with the global namespace included to get our new shiny function!
    * There are `AI_IMPLEMENT_RETRY_LIMIT` amount of retries to the LLM for getting the function definition `exec` call not throw a syntax error.

3. **Caching**: If `CURSED_VIBING_CACHE_ENABLED` is `True`, the compiled function is cached in memory.
    * **Subsequent calls** to the function then use the cached implementation immediately.
    * If you restart the script, the cache is lost and the LLM will be called again, regardless of `CURSED_VIBING_CACHE_ENABLED`.

## Why?

A colleague shared the following meme:

<img src="./img/meme.png" width="400" alt="Developers in 2020 vs 2024">

([source](https://www.reddit.com/r/AICompanions/comments/1ph8w96/developers_in_2020/)) in a chat and I thought that surely as an Agent Developer I can do better than that.

## TODO

1. It seem very inefficient that a failed parsing of a function leads to a vanilla retry call. We should have a more complex retry logic where we continue the discussion with the LLM, giving it the syntax errors as context.
2. A more flexible LLM-integration supporting also local models would be great!

