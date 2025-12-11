"""
Cursed decorator that implements functions by asking OpenAI what they should do.

Supports rich type hints including Annotated descriptions and Pydantic schemas.
"""

import inspect
import json
import os
import re
from functools import wraps
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

# ============ CONFIGURATION ============

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()  # Uses OPENAI_API_KEY env var
    return _client


_implementation_cache: dict[str, callable] = {}
_RETRY_LIMIT = int(os.environ.get("AI_IMPLEMENT_RETRY_LIMIT", 3))


# ============ TYPE EXTRACTION HELPERS ============


def _extract_param_info(func) -> dict[str, dict[str, Any]]:
    """Extract rich parameter metadata including Annotated descriptions and Pydantic schemas."""
    hints = get_type_hints(func, include_extras=True)
    sig = inspect.signature(func)
    params = {}

    for name, param in sig.parameters.items():
        info = {"name": name}
        hint = hints.get(name)

        if hint is None:
            info["type"] = "Any"
        elif get_origin(hint) is Annotated:
            info.update(_extract_annotated_info(hint))
        elif isinstance(hint, type) and issubclass(hint, BaseModel):
            info["type"] = hint.__name__
            info["schema"] = hint.model_json_schema()
        else:
            info["type"] = getattr(hint, "__name__", str(hint))

        if param.default is not inspect.Parameter.empty:
            info["default"] = repr(param.default)

        params[name] = info

    return params


def _extract_annotated_info(hint) -> dict[str, Any]:
    """Extract type and metadata from an Annotated type hint."""
    args = get_args(hint)
    base_type = args[0]
    metadata = args[1:]

    info = {}

    # Handle Pydantic models
    if isinstance(base_type, type) and issubclass(base_type, BaseModel):
        info["type"] = base_type.__name__
        info["schema"] = base_type.model_json_schema()
    else:
        info["type"] = getattr(base_type, "__name__", str(base_type))

    # Extract descriptions from metadata
    for m in metadata:
        if isinstance(m, str):
            info["description"] = m
        elif isinstance(m, FieldInfo) and m.description:
            info["description"] = m.description

    return info


def _extract_return_info(func) -> dict[str, Any]:
    """Extract return type info, including Pydantic schema if applicable."""
    hints = get_type_hints(func, include_extras=True)
    ret = hints.get("return")

    if ret is None:
        return {"type": "Any"}

    if get_origin(ret) is Annotated:
        args = get_args(ret)
        base_type = args[0]
        info = {"type": getattr(base_type, "__name__", str(base_type))}
        for m in args[1:]:
            if isinstance(m, str):
                info["description"] = m
        if isinstance(base_type, type) and issubclass(base_type, BaseModel):
            info["schema"] = base_type.model_json_schema()
        return info

    if isinstance(ret, type) and issubclass(ret, BaseModel):
        return {"type": ret.__name__, "schema": ret.model_json_schema()}

    return {"type": getattr(ret, "__name__", str(ret))}


# ============ PROMPT BUILDING ============


def _build_prompt(func) -> str:
    """Build a detailed prompt from function metadata."""
    name = func.__name__
    doc = inspect.getdoc(func) or ""
    params = _extract_param_info(func)
    ret = _extract_return_info(func)
    sig = inspect.signature(func)

    lines = [
        "Implement this Python function:\n",
        f"def {name}{sig}:",
    ]

    if doc:
        lines.append(f'    """{doc}"""')

    lines.append("\nParameter details:")
    for pname, pinfo in params.items():
        lines.extend(_format_param_info(pname, pinfo))

    lines.extend(_format_return_info(ret))
    lines.append(
        "\nReturn ONLY the function body. No def line, no docstring, no markdown."
    )

    return "\n".join(lines)


def _format_param_info(name: str, info: dict[str, Any]) -> list[str]:
    """Format a single parameter's info for the prompt."""
    lines = []
    desc = f"  - {name}: {info['type']}"
    if "description" in info:
        desc += f" — {info['description']}"
    if "default" in info:
        desc += f" (default: {info['default']})"
    lines.append(desc)

    if "schema" in info:
        lines.append(f"    Schema: {json.dumps(info['schema'], indent=2)}")

    return lines


def _format_return_info(ret: dict[str, Any]) -> list[str]:
    """Format return type info for the prompt."""
    lines = [f"\nReturn type: {ret['type']}"]
    if "description" in ret:
        lines.append(f"  Description: {ret['description']}")
    if "schema" in ret:
        lines.append(f"  Schema: {json.dumps(ret['schema'], indent=2)}")
    return lines


# ============ CODE GENERATION ============


def _strip_markdown(code: str) -> str:
    """Remove ```python ... ``` wrappers if present."""
    code = re.sub(r"^```(?:python)?\s*\n?", "", code)
    code = re.sub(r"\n?```\s*$", "", code)
    return code.strip()


def _build_full_code(func_name: str, sig, docstring: str, body_code: str) -> str:
    """Reconstruct the full function code from its parts."""
    full_code = f"def {func_name}{sig}:\n"
    if docstring:
        full_code += f'    """{docstring}"""\n'
    for line in body_code.split("\n"):
        full_code += f"    {line}\n" if line.strip() else "\n"
    return full_code


def _generate_implementation(func):
    """Generate an implementation for the given function stub using OpenAI."""
    func_name = func.__name__
    sig = inspect.signature(func)
    docstring = inspect.getdoc(func) or ""
    prompt = _build_prompt(func)

    print(f"📝 Prompt for {func_name}:\n{prompt}\n{'=' * 50}")

    last_error = None
    for attempt in range(_RETRY_LIMIT):
        try:
            response = _get_client().chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
            )

            body_code = response.choices[0].message.content.strip()
            body_code = _strip_markdown(body_code)

            full_code = _build_full_code(func_name, sig, docstring, body_code)
            print(f"🤖 Generated implementation for {func_name}:\n{full_code}")

            # Execute in isolated namespace with required types available
            namespace = {"BaseModel": BaseModel, "Field": Field, "Annotated": Annotated}
            exec(full_code, namespace)
            
            # Attach stats
            implemented_func = namespace[func_name]
            implemented_func._ai_stats = {"attempts": attempt + 1}
            return implemented_func

        except Exception as e:
            last_error = e
            print(
                f"⚠️  Attempt {attempt + 1}/{_RETRY_LIMIT} failed for {func_name}: {e}"
            )
            if attempt + 1 == _RETRY_LIMIT:
                raise RuntimeError(
                    f"Failed to generate implementation for {func_name} "
                    f"after {_RETRY_LIMIT} attempts"
                ) from last_error


# ============ THE DECORATOR ============


def ai_implement(func):
    """
    Decorator that replaces a stub function with an AI-generated implementation.

    Supports:
    - Basic type hints (int, str, float, etc.)
    - Annotated types with descriptions
    - Pydantic models with full schema extraction

    Usage:
        @ai_implement
        def calculate_sum(
            a: Annotated[int, "First number"],
            b: Annotated[int, "Second number"],
        ) -> int:
            '''Add two numbers.'''
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__

        if func_name not in _implementation_cache:
            _implementation_cache[func_name] = _generate_implementation(func)

        return _implementation_cache[func_name](*args, **kwargs)

    return wrapper

