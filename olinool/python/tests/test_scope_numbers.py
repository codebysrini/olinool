"""JSON double-safe numeric limits rule (v0.3, design §9).

Limit values must be IEEE-754-exact so a JS/TS verifier (float64) and a Python
verifier agree on the `>` comparison that decides attenuation. Verdict-neutral
on the frozen corpus (limits {5,10,25,50,500}); this pins the new boundary.
"""
from __future__ import annotations

import pytest

from olinool.scopes import MAX_SAFE_LIMIT, ScopeError, validate_scope


def _scope(v):
    return [{"act": "read", "res": "d/*", "limits": {"amount": v}}]


@pytest.mark.parametrize("v", [0, 5, 500, 2 ** 53])
def test_safe_limits_accepted(v):
    validate_scope(_scope(v))  # no raise


@pytest.mark.parametrize("v", [2 ** 53 + 1, 10 ** 30, float("inf"), float("nan")])
def test_unsafe_limits_rejected(v):
    with pytest.raises(ScopeError):
        validate_scope(_scope(v))


def test_finite_safe_float_ok():
    validate_scope(_scope(0.5))  # finite, in range -> allowed (same bits in JS)


def test_max_safe_boundary():
    validate_scope(_scope(MAX_SAFE_LIMIT))          # 2**53 allowed
    with pytest.raises(ScopeError):
        validate_scope(_scope(MAX_SAFE_LIMIT + 1))  # beyond -> rejected
