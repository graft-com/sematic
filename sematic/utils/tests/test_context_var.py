# Copyright © 2021-Present Graft Inc. <copyright@graft.com>
"""Module providing tests of the ContextVar utilities."""

# Standard Library
from contextvars import ContextVar

# Sematic
# Graft
from sematic.utils.context_var import temp_set_context_vars


_DEFAULT_VALUE = 0
_test_ctx_var: ContextVar[int] = ContextVar("test_ctx_var", default=_DEFAULT_VALUE)


def test_temp_set_context_vars():
    """Test the temp_set_context_vars API."""
    assert _test_ctx_var.get() == _DEFAULT_VALUE
    new_value = 1
    with temp_set_context_vars({_test_ctx_var: new_value}):
        assert _test_ctx_var.get() == new_value
    assert _test_ctx_var.get() == _DEFAULT_VALUE
