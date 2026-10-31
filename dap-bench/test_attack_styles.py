"""Guards for the T3 attack-style taxonomy (AgentDojo-derived).

Run: python3 -m pytest dap-bench/test_attack_styles.py -q
(or plain `python3 dap-bench/test_attack_styles.py` — has a __main__ shim).

These are structural guards, not model runs: they assert the taxonomy stays
complete, every style carries a source citation (provenance can't rot), each
style actually plants the canary, and — critically — that a named style never
perturbs the FROZEN default suite.
"""
from __future__ import annotations

import hashlib
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from tasks import ATTACK_STYLES, CANARY, _apply_style, build_tasks

# The six styles the handoff (B4 NO-GO fallback) requires, each mapped to the
# AgentDojo/AgentLure taxonomy.
REQUIRED_STYLES = {
    "direct_instruction",
    "tool_output_injection",
    "exfil_lure",
    "role_confusion",
    "payload_splitting",
    "format_hijack",
}


def test_taxonomy_covers_required_styles():
    assert REQUIRED_STYLES <= set(ATTACK_STYLES), (
        f"missing styles: {REQUIRED_STYLES - set(ATTACK_STYLES)}")
    assert len(ATTACK_STYLES) >= 6


def test_every_style_has_a_source_citation():
    for name, spec in ATTACK_STYLES.items():
        assert spec.get("source"), f"style {name!r} has no source citation"


def test_every_style_plants_the_canary():
    # payload_splitting is the deliberate exception: it never emits the literal
    # token (that's the whole point), it emits the two halves.
    for name in ATTACK_STYLES:
        payload = _apply_style(name, CANARY)
        if name == "payload_splitting":
            half = len(CANARY) // 2
            assert CANARY[:half] in payload and CANARY[half:] in payload
            assert CANARY not in payload  # literal token must NOT appear whole
        else:
            assert CANARY in payload, f"style {name!r} did not plant the canary"


def _suite_hash(**kwargs) -> str:
    ts = build_tasks(12, seed=7, **kwargs)
    blob = json.dumps(
        [(t.tid, t.goal, t.docs, t.required_facts, t.injected, t.injection_class) for t in ts],
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def test_default_suite_is_frozen_regardless_of_styles_existing():
    # Adding the style machinery must not move the default suite. Independently
    # proven byte-identical to the pre-B4 HEAD via subprocess diff (outside +
    # declared); this hash pins that state for regression.
    assert _suite_hash() == (
        "d1ce23a79ae3023b13bad56970b2734a5ff5196c627225949c84ca33002f3ad9"
    ), "DEFAULT SUITE CHANGED — frozen-corpus violation"


def test_named_style_changes_the_suite_but_only_when_asked():
    base = _suite_hash()
    for name in ATTACK_STYLES:
        assert _suite_hash(attack_style=name) != base, (
            f"style {name!r} produced the default suite (payload not applied)")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} attack-style guards passed")
