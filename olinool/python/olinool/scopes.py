"""olinool.scopes — the scope algebra and the subset (attenuation) relation.

This is the piece every governance sketch hand-waves. Two independent
implementations must compute the *same* `is_subset` answer or interop dies,
so the algebra is deliberately small and total:

A Scope is a list of Grants. A Grant is:
    {
      "act":    "<verb>" | "*",          # exact action token or full wildcard
      "res":    "<resource-pattern>",     # prefix-glob: literal, or literal + "*" at END only
      "limits": {"<key>": <number>, ...}  # optional numeric ceilings (e.g. amount)
    }

child_scope ⊆ parent_scope  iff  every child grant is covered by at least
one parent grant.  Coverage rules:

  act:  parent "*" covers anything; otherwise strings must be equal.
        A child "*" is only covered by a parent "*".
  res:  patterns may contain at most one "*", only as the final character.
        parent "db/*"  covers  "db/eu", "db/eu/*", "db/*"
        parent "db/eu" covers  only "db/eu"
        A child pattern ending in "*" needs a parent pattern ending in "*"
        whose prefix is a prefix of the child's prefix.
  limits: for EVERY limit key present in the parent grant, the child grant
        MUST carry the same key with value <= parent value. A child missing
        a parent's limit key is unbounded on that key => NOT covered.
        Child may add extra keys (further restriction).

Anything outside this grammar is a structural error, not "allow".
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

Grant = Dict[str, Any]
Scope = List[Grant]

# JSON double-safe bound (v0.3): limit values must be IEEE-754-exact so a JS/TS
# verifier (all numbers float64) and a Python verifier compute the SAME `>`
# comparison. Integers up to 2**53 are exactly representable; beyond that a
# JS impl silently rounds and two verifiers could disagree on attenuation.
MAX_SAFE_LIMIT = 2 ** 53


class ScopeError(ValueError):
    pass


def validate_scope(scope: Any) -> None:
    if not isinstance(scope, list) or not scope:
        raise ScopeError("scope must be a non-empty list of grants")
    for g in scope:
        if not isinstance(g, dict):
            raise ScopeError("grant must be an object")
        extra = set(g.keys()) - {"act", "res", "limits"}
        if extra:
            raise ScopeError(f"unknown grant fields: {sorted(extra)}")
        act, res = g.get("act"), g.get("res")
        if not isinstance(act, str) or not act:
            raise ScopeError("grant.act must be a non-empty string")
        if not isinstance(res, str) or not res:
            raise ScopeError("grant.res must be a non-empty string")
        star = res.count("*")
        if star > 1 or (star == 1 and not res.endswith("*")):
            raise ScopeError(f"grant.res may contain '*' only as final char: {res!r}")
        limits = g.get("limits", {})
        if not isinstance(limits, dict):
            raise ScopeError("grant.limits must be an object")
        for k, v in limits.items():
            if not isinstance(k, str) or not isinstance(v, (int, float)) or isinstance(v, bool):
                raise ScopeError("limits must map string keys to numbers")
            if isinstance(v, float) and not math.isfinite(v):
                raise ScopeError("limit values must be finite (no NaN/Infinity)")
            if abs(v) > MAX_SAFE_LIMIT:
                raise ScopeError(f"limit values must be IEEE-754 double-safe (|v| <= 2**53): {v!r}")
            if v < 0:
                raise ScopeError("limit values must be >= 0")


def _act_covers(parent: str, child: str) -> bool:
    if parent == "*":
        return True
    return parent == child


def _res_covers(parent: str, child: str) -> bool:
    if parent.endswith("*"):
        prefix = parent[:-1]
        if child.endswith("*"):
            return child[:-1].startswith(prefix)
        return child.startswith(prefix)
    return parent == child  # literal parent covers only the identical literal


def _limits_cover(parent: Dict[str, Any], child: Dict[str, Any]) -> bool:
    for key, pval in parent.items():
        if key not in child:
            return False  # child unbounded where parent was bounded
        if child[key] > pval:
            return False
    return True


def grant_covers(parent: Grant, child: Grant) -> bool:
    return (
        _act_covers(parent["act"], child["act"])
        and _res_covers(parent["res"], child["res"])
        and _limits_cover(parent.get("limits", {}), child.get("limits", {}))
    )


def is_subset(child: Scope, parent: Scope) -> bool:
    """True iff every child grant is covered by >= 1 parent grant."""
    validate_scope(child)
    validate_scope(parent)
    return all(any(grant_covers(p, c) for p in parent) for c in child)


def grant_permits(scope: Scope, act: str, res: str, spend: Dict[str, float] | None = None) -> bool:
    """Would this scope permit a concrete action? (Used by receivers post-verify.)

    `res` here is a concrete resource (no wildcard). `spend` are the numeric
    quantities of this single action, checked against per-grant ceilings.
    NOTE: cumulative spend across actions requires external state by design.
    """
    for g in scope:
        if not _act_covers(g["act"], act):
            continue
        if not _res_covers(g["res"], res):
            continue
        limits = g.get("limits", {})
        ok = True
        for k, v in (spend or {}).items():
            if k in limits and v > limits[k]:
                ok = False
                break
        if ok:
            return True
    return False
