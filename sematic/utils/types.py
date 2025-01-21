# Standard Library
from typing import (
    Any,
    Generic,
    Optional,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from typing_extensions import get_original_bases


def as_bool(value: Optional[Any]) -> bool:
    """
    Returns a boolean interpretation of the contents of the specified value.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    str_value = str(value)
    if len(str_value) == 0:
        return False

    return bool(strtobool(str_value))


# Implementation of strtobool from: https://github.com/drgarcia1986/simple-settings
_MAP = {
    "y": True,
    "yes": True,
    "t": True,
    "true": True,
    "on": True,
    "1": True,
    "n": False,
    "no": False,
    "f": False,
    "false": False,
    "off": False,
    "0": False,
}


def strtobool(value):
    try:
        return _MAP[str(value).lower()]
    except KeyError:
        raise ValueError('"{}" is not a valid bool value'.format(value))


def resolve_type(cls: type, attribute: str):
    """Resolve the type of an attribute on an input class.

    Handles situation where attribute is a TypeVar.
    """
    # Extract the attribute's type hint
    type_hints = get_type_hints(cls)
    try:
        field_type = type_hints[attribute]
    except KeyError:
        error_msg = (
            f"The class '{cls.__name__}' does not have the '{attribute}' attribute"
        )
        raise ValueError(error_msg)
    # And if it's a TypeVar....
    if isinstance(field_type, TypeVar):
        # Iterate through the bases to find the matching original type
        for base in get_original_bases(cls):
            origin = get_origin(base)
            if origin is None:
                raise ValueError(f"Found no origin for the base: {base.__name__}")
            elif origin is Generic:
                error_msg = f"The annotation for '{attribute}' has not been parametrized"
                raise ValueError(error_msg)
            else:
                type_args = get_args(base)
                # Map TypeVars to their actual types
                type_var_mapping = dict(zip(origin.__parameters__, type_args))
                if field_type in type_var_mapping:
                    return type_var_mapping[field_type]
    return field_type
