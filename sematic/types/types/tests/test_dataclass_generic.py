"""Module providing tests of Dataclass support for Generic dataclasses."""

# Standard Library
import re

# Third-party
import sys
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import pytest
from typing_extensions import get_original_bases

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.serialization import (
    type_from_json_encodable,
    type_to_json_encodable,
)


T = TypeVar("T")


@dataclass
class HasGeneric(Generic[T]):
    x: T


@dataclass
class DerivedIntHasGeneric(HasGeneric[int]):
    pass


@dataclass
class DerivedFloatHasGeneric(HasGeneric[float]):
    pass


@dataclass
class DerivedStrHasGeneric(HasGeneric[str]):
    pass


@dataclass
class DerivedIntListHasGeneric(HasGeneric[list[int]]):
    pass


@pytest.mark.parametrize(
    "from_type, to_type, expected_can_cast, expected_error",
    (
        # When the underlying types can cast to one another, it's fine
        (
            DerivedIntHasGeneric,
            DerivedFloatHasGeneric,
            True,
            None,
        ),
        (
            DerivedFloatHasGeneric,
            DerivedIntHasGeneric,
            True,
            None,
        ),
        # But if the types can't cast, it breaks
        (
            DerivedFloatHasGeneric,
            DerivedStrHasGeneric,
            False,
            (
                r"Cannot cast.*DerivedFloatHasGeneric.*to.*DerivedStrHasGeneric.*"
                r"field 'x' cannot cast.*float.*cannot cast.*str"
            ),
        ),
        (
            DerivedIntHasGeneric,
            DerivedIntListHasGeneric,
            False,
            (
                r"Cannot cast.*DerivedIntHasGeneric.*to.*DerivedIntListHasGeneric.*"
                r"field 'x' cannot cast.*int.*to list.*int.*"
            ),
        ),
    ),
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast, error
    if expected_error is None:
        assert error is None
    else:
        assert re.match(expected_error, error)


@pytest.mark.parametrize(
    "value, type_, expected_type, expected_value, expected_error",
    (
        # When the underlying types can cast to one another, it's fine
        (
            DerivedIntHasGeneric(x=1),
            DerivedFloatHasGeneric,
            DerivedFloatHasGeneric,
            DerivedFloatHasGeneric(x=1.0),
            None,
        ),
        (
            DerivedFloatHasGeneric(x=1.0),
            DerivedIntHasGeneric,
            DerivedIntHasGeneric,
            DerivedIntHasGeneric(x=1),
            None,
        ),
        # But if the types can't cast, it breaks
        (
            DerivedFloatHasGeneric(x=1),
            DerivedStrHasGeneric,
            DerivedStrHasGeneric,
            None,
            (
                r"Cannot cast field 'x' of DerivedFloatHasGeneric.*to.*"
                r"DerivedStrHasGeneric.*Cannot cast 1 to.*str"
            ),
        ),
        (
            DerivedIntHasGeneric(x=1),
            DerivedIntListHasGeneric,
            DerivedIntListHasGeneric,
            None,
            (
                r"Cannot cast field 'x' of DerivedIntHasGeneric.*to.*"
                r"DerivedIntListHasGeneric.*1 not an iterable"
            ),
        ),
    ),
)
def test_safe_cast(
    value: Any, type_: type, expected_type: type, expected_value: Any, expected_error: str
):
    cast_value, error = safe_cast(value, type_)
    if expected_error is None:
        assert isinstance(cast_value, expected_type), error
        assert cast_value == expected_value
        assert error is None
    else:
        assert error is not None
        assert re.match(expected_error, error)


def test_type_to_json_encodable():
    """Test casting a dataclass to JSON-encodable."""
    result = type_to_json_encodable(DerivedIntHasGeneric)
    category, key, parameters = result["type"]
    assert category == "dataclass"
    assert key == DerivedIntHasGeneric.__name__
    expected_parameters = {
        "import_path": DerivedIntHasGeneric.__module__,
        "fields": {"x": {"type": ("builtin", "int", {})}},
    }
    assert parameters == expected_parameters
    registry = result["registry"]
    major, minor, *_ = sys.version_info
    if minor >= 10:
        for base in get_original_bases(DerivedIntHasGeneric):
            assert base.__name__ not in registry


@dataclass
class HasDerivedGeneric:
    derived_generic: DerivedIntHasGeneric


GENERIC_TYPES_TO_TEST = (
    DerivedIntHasGeneric,
    DerivedFloatHasGeneric,
    DerivedStrHasGeneric,
    DerivedIntListHasGeneric,
    HasDerivedGeneric,
)


@pytest.mark.parametrize(
    "type_",
    GENERIC_TYPES_TO_TEST,
)
def test_type_from_json_encodable(type_: type):
    json_encodable = type_to_json_encodable(type_)
    assert type_from_json_encodable(json_encodable) is type_
