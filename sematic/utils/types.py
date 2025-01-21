# Standard Library
from typing import (
    Any,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
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
    return _resolve_generic_type(cls=cls, type_=field_type, attribute=attribute)


def _resolve_generic_type(
    cls: type, type_: Union[type, TypeVar], attribute: str
) -> Union[type, TypeVar]:
    origin = get_origin(type_)
    if origin is not None:  # It's a generic like list, dict, etc.
        if origin is Union:
            resolved_args = tuple(
                _resolve_generic_type(cls, arg, attribute) for arg in get_args(type_)
            )
            return cast(type, Union[resolved_args])
        args = tuple(
            _resolve_generic_type(cls=cls, type_=arg, attribute=attribute)
            for arg in get_args(type_)
        )
        return origin[args] if args else origin
    elif isinstance(type_, TypeVar):  # Resolve TypeVar
        # Resolve the TypeVar from the class's __orig_bases__
        for base in get_original_bases(cls):
            base_origin = get_origin(base)
            if base_origin is None:
                raise ValueError(f"Found no origin for the base: {base.__name__}")
            elif base_origin is Generic:
                error_msg = f"The annotation for '{attribute}' has not been parametrized"
                raise ValueError(error_msg)
            else:
                type_args = get_args(base)
                type_var_mapping = dict(zip(base_origin.__parameters__, type_args))
                if type_ in type_var_mapping:
                    return type_var_mapping[type_]
        # Unresolved TypeVar
        return type_
    else:
        # Non-generic type (e.g., int, str)
        return type_
