"""Template variable substitution and JSONPath extraction for SOP execution.

Replaces {{variable}} placeholders in SOP step definitions with runtime values.
Extracts values from API responses using simplified JSONPath expressions.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Pattern for template variables: {{variable_name}}
TEMPLATE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def resolve_templates(obj: Any, context: dict[str, Any]) -> Any:
    """Recursively replace {{variable}} placeholders in a structure.

    Handles strings, dicts, lists, and passthrough for other types.

    Args:
        obj: The object containing potential template variables.
        context: Key-value pairs for substitution.

    Returns:
        The object with all template variables resolved.
    """
    if isinstance(obj, str):
        return _resolve_string(obj, context)
    elif isinstance(obj, dict):
        return {k: resolve_templates(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_templates(item, context) for item in obj]
    else:
        return obj


def _resolve_string(template: str, context: dict[str, Any]) -> str:
    """Replace all {{variable}} occurrences in a string."""
    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in context:
            return str(context[var_name])
        # Leave unresolved variables as-is
        logger.debug("Unresolved template variable: %s", var_name)
        return match.group(0)

    return TEMPLATE_PATTERN.sub(replacer, template)


def evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    """Evaluate a simple condition string with template substitution.

    Supports: "{{var}} == 'value'", "{{var}} != 'value'"
    """
    resolved = _resolve_string(condition, context)

    # Try == operator
    if " == " in resolved:
        left, right = resolved.split(" == ", 1)
        return left.strip().strip("'\"") == right.strip().strip("'\"")

    # Try != operator
    if " != " in resolved:
        left, right = resolved.split(" != ", 1)
        return left.strip().strip("'\"") != right.strip().strip("'\"")

    # Try > < >= <= for numeric comparisons
    for op in [">=", "<=", ">", "<"]:
        if f" {op} " in resolved:
            left, right = resolved.split(f" {op} ", 1)
            try:
                lv, rv = float(left.strip()), float(right.strip())
                return eval(f"{lv} {op} {rv}")  # noqa: S307
            except ValueError:
                return False

    # Non-empty string is truthy
    return bool(resolved.strip())


def extract_jsonpath(data: Any, path: str) -> Any:
    """Extract value from nested data using a simplified JSONPath.

    Supports:
        $.data.token           -> data["data"]["token"]
        $.data.items[0].id     -> data["data"]["items"][0]["id"]
        $.results[2].name      -> data["results"][2]["name"]

    Args:
        data: The response data (typically a dict).
        path: JSONPath-like expression starting with $. or just dot-separated.

    Returns:
        The extracted value.

    Raises:
        KeyError: If the path does not exist.
        IndexError: If array index is out of range.
    """
    # Remove leading $. if present
    if path.startswith("$."):
        path = path[2:]
    elif path.startswith("$"):
        path = path[1:]

    if not path:
        return data

    parts = _parse_path(path)
    current = data
    for part in parts:
        if isinstance(part, int):
            current = current[part]
        else:
            current = current[part]
    return current


def _parse_path(path: str) -> list[str | int]:
    """Parse a dot-separated path with optional array indices into parts.

    Examples:
        "data.token" -> ["data", "token"]
        "data.items[0].id" -> ["data", "items", 0, "id"]
        "results[2].name" -> ["results", 2, "name"]
    """
    parts: list[str | int] = []
    for segment in path.split("."):
        if not segment:
            continue
        # Check for array index: items[0]
        if "[" in segment:
            key, rest = segment.split("[", 1)
            if key:
                parts.append(key)
            # Handle multiple indices (unlikely but safe)
            for idx_str in rest.split("]")[:-1]:  # Last split is empty
                if idx_str:
                    parts.append(int(idx_str))
        else:
            parts.append(segment)
    return parts


def extract_variables(
    data: Any,
    extractions: dict[str, str],
) -> dict[str, Any]:
    """Extract multiple variables from response data using JSONPath expressions.

    Args:
        data: The response data.
        extractions: Mapping of variable_name -> jsonpath_expression.

    Returns:
        Dict of extracted variable name -> value. Missing paths are skipped with a warning.
    """
    result: dict[str, Any] = {}
    for var_name, path in extractions.items():
        try:
            result[var_name] = extract_jsonpath(data, path)
        except (KeyError, IndexError, TypeError) as e:
            logger.warning("Failed to extract '%s' from path '%s': %s", var_name, path, e)
    return result
