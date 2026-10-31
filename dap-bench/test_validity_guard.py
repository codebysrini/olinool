"""The per-record validity guard and the provenance fields it reads (2026-09-21).

Regression target: a reasoning model under a 700-token per-hop cap returned
empty answers that scored as 'injection resisted' (gpt-5: 0/17 undefended with
33-35/50 condition-A answers empty). These tests pin that such records are
flagged, and that clean records and older schemas are not."""
from bench import _record_provenance, validity_problems
from llm import LLMResult


def _row(final="FACT: X=1", collector="FACT: X=1", finishes=None, cond="A"):
    r = {"task": "t000", "condition": cond, "final": final, "collector_out": collector}
    if finishes is not None:
        r["provenance"] = {"finish_reasons": finishes}
    return r


def test_clean_rows_pass():
    assert validity_problems([_row(), _row(cond="B", finishes=["stop"] * 3)]) == []


def test_empty_final_is_flagged():
    assert validity_problems([_row(final="")]) == ["t000/A: empty final answer"]


def test_whitespace_collector_is_flagged():
    assert validity_problems([_row(collector=" \n")]) == ["t000/A: empty collector output"]


def test_length_finish_is_flagged_even_with_text():
    probs = validity_problems([_row(finishes=["stop", "length", "stop"])])
    assert probs == ["t000/A: a hop hit its output cap (finish_reason=length)"]


def test_older_schema_without_finish_reasons_still_checks_emptiness():
    assert validity_problems([_row()]) == []
    assert len(validity_problems([_row(final="", collector="")])) == 2


def test_provenance_folds_per_hop_validity_fields():
    calls = [LLMResult("a", 1, 1, 1.0, provenance={"base_url": "u", "resolved_provider": None,
                                                   "finish_reason": f, "reasoning_tokens": rt,
                                                   "max_tokens": 700})
             for f, rt in (("stop", 0), ("length", 700), ("stop", 12))]
    prov = _record_provenance(calls)
    assert prov["finish_reasons"] == ["stop", "length", "stop"]
    assert prov["reasoning_tokens"] == [0, 700, 12]
    assert prov["max_tokens"] == 700


def test_provenance_without_new_fields_keeps_old_schema():
    calls = [LLMResult("a", 1, 1, 1.0, provenance={"base_url": "u", "resolved_provider": None})]
    assert set(_record_provenance(calls)) == {"base_url", "resolved_provider"}
