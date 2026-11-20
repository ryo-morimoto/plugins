"""A small JSON Schema 2020-12 validator, limited to the keywords te's schema uses.

Supported: type, enum, const, required, properties, additionalProperties (bool or schema),
minProperties, maxProperties, items, minItems, minLength, pattern, minimum, maximum,
anyOf, allOf, if/then, $ref (local JSON pointers only). Unknown keywords raise, so a schema
that relies on something unsupported fails loudly instead of passing silently.
Full validation against the official spec can be run in CI with an external validator.
"""

from __future__ import annotations

import re
from typing import Any

SUPPORTED = {
    "$schema", "$id", "$defs", "title", "description",
    "type", "enum", "const", "required", "properties", "additionalProperties",
    "minProperties", "maxProperties", "items", "minItems", "minLength", "pattern",
    "minimum", "maximum", "anyOf", "allOf", "if", "then", "$ref",
}

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate(instance: Any, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    """Return a list of error messages; empty means valid."""
    root = root if root is not None else schema
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise ValueError(f"unsupported schema keywords at {path}: {sorted(unknown)}")
    errs: list[str] = []

    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"only local references are supported: {ref}")
        target = root
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        errs += validate(instance, target, root, path)

    t = schema.get("type")
    if t is not None and not _TYPES[t](instance):
        return errs + [f"{path}: expected {t}"]
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: must be one of {schema['enum']}")
    if "const" in schema and instance != schema["const"]:
        errs.append(f"{path}: must be {schema['const']!r}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errs.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                errs += validate(value, props[key], root, f"{path}.{key}")
            else:
                extra = schema.get("additionalProperties", True)
                if extra is False:
                    errs.append(f"{path}: unknown field {key!r}")
                elif isinstance(extra, dict):
                    errs += validate(value, extra, root, f"{path}.{key}")
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            errs.append(f"{path}: needs at least {schema['minProperties']} fields")
        if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
            errs.append(f"{path}: allows at most {schema['maxProperties']} fields")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errs.append(f"{path}: needs at least {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(instance):
                errs += validate(item, schema["items"], root, f"{path}[{i}]")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errs.append(f"{path}: must not be empty")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errs.append(f"{path}: does not match {schema['pattern']}")

    if _TYPES["number"](instance):
        if "minimum" in schema and instance < schema["minimum"]:
            errs.append(f"{path}: must be >= {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errs.append(f"{path}: must be <= {schema['maximum']}")

    if "anyOf" in schema:
        if not any(not validate(instance, s, root, path) for s in schema["anyOf"]):
            errs.append(f"{path}: matches none of the allowed forms")
    for sub in schema.get("allOf", []):
        if "if" in sub:
            if not validate(instance, sub["if"], root, path):
                errs += validate(instance, sub.get("then", {}), root, path)
        else:
            errs += validate(instance, sub, root, path)
    if "if" in schema and not validate(instance, schema["if"], root, path):
        errs += validate(instance, schema.get("then", {}), root, path)
    return errs
