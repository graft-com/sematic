# Standard Library
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

# Third-party
import pytest

# Sematic
from sematic.utils.types import resolve_type


T = TypeVar("T")
U = TypeVar("U")


def test_resolve_type_for_basic_type():
    """Test the resolve_type utility."""

    @dataclass
    class A(Generic[T, U]):
        val: T
        union_val: Union[T, U]

        def test(self, a: T) -> T:
            return self.val

    @dataclass
    class B(A[int, float]):
        def test(self, a: int) -> int:
            return a + self.val

    @dataclass
    class C(A[A[int, float], float]):
        pass

    @dataclass
    class Concrete:
        x: int

    @dataclass
    class HasUnion:
        union: Union[int, str]

    assert resolve_type(B, "val") is int
    assert resolve_type(B, "union_val") is Union[int, float]
    assert resolve_type(C, "val") is A[int, float]
    assert resolve_type(Concrete, "x") is int
    assert resolve_type(HasUnion, "union") is Union[int, str]
    for cls, attr_name, match in (
        (
            A,
            "val",
            "The annotation for 'val' has not been parametrized",
        ),
        (Concrete, "y", "The class 'Concrete' does not have the 'y' attribute"),
    ):
        with pytest.raises(ValueError, match=match):
            resolve_type(cls, attr_name)


def test_resolve_type_for_container_types():
    """Test the resolve_type utility."""

    @dataclass
    class HasContainers(Generic[T, U]):
        items_list: list[T]
        items_tuple: tuple[T]
        items_set: set[T]
        maps: dict[T, U]

    @dataclass
    class IntFloat(HasContainers[int, float]):
        pass

    @dataclass
    class Nested(HasContainers[int, HasContainers[int, float]]):
        pass

    assert resolve_type(IntFloat, "items_list") == list[int]
    assert resolve_type(IntFloat, "items_tuple") == tuple[int]
    assert resolve_type(IntFloat, "items_set") == set[int]
    assert resolve_type(IntFloat, "maps") == dict[int, float]
    assert resolve_type(Nested, "maps") == dict[int, HasContainers[int, float]]
