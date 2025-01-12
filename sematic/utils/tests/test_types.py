# Standard Library
from dataclasses import dataclass
from typing import Generic, TypeVar

# Third-party
import pytest

# Sematic
from sematic.utils.types import resolve_type


def test_resolve_type():
    """Test the resolve_type utility."""

    T = TypeVar("T")

    @dataclass
    class A(Generic[T]):
        val: T

        def test(self, a: T) -> T:
            return self.val

    @dataclass
    class B(A[int]):
        def test(self, a: int) -> int:
            return a + self.val

    @dataclass
    class C(A[A[int]]):
        pass

    @dataclass
    class Concrete:
        x: int

    assert resolve_type(B, "val") is int
    assert resolve_type(C, "val") is A[int]
    assert resolve_type(Concrete, "x") is int
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
