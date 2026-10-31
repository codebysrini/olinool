#!/usr/bin/env python3
"""dap-bench runner.

Mechanics check (free, no key):    python3 run.py --backend mock --n 12
Real run (needs ANTHROPIC_API_KEY): python3 run.py --backend claude --n 12
Cheap first real run:               python3 run.py --backend claude --n 4

Writes results/raw_<backend>.jsonl and results/results_<backend>.md.
Cost control: token totals are printed; multiply by your account's rates
(rates change — check the pricing page, don't trust hardcoded numbers).
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import platform
import re
import subprocess
import sys

from bench import run_task, summarize, validity_problems
from llm import make_backend
from tasks import build_tasks

HERE = pathlib.Path(__file__).resolve().parent
HARNESS_FILES = ("run.py", "bench.py", "bench_dabba.py", "bench_dabba_vh.py", "llm.py", "tasks.py")


def _manifest(args, stem: str, status: str, problems: list) -> dict:
    """Per-run configuration record written beside the raw file (added
    2026-09-21): model, serving path, decoding and cap settings, and the exact
    harness commit -- so a lane's configuration never has to be reconstructed
    from memory. Never contains credentials (keys live only in the env)."""
    def git(*a):
        try:
            p = subprocess.run(["git", "-C", str(HERE), *a], capture_output=True,
                               text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout.strip() if p.returncode == 0 else None
    dirty = git("status", "--porcelain", "--", *HARNESS_FILES)
    return {
        "stem": stem, "status": status, "problems": problems[:50],
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv[1:], "harness_commit": git("rev-parse", "HEAD"),
        "harness_files_modified": bool(dirty) if dirty is not None else None,
        "python": platform.python_version(), "backend": args.backend, "model": args.model,
        "base_url": args.base_url, "gateway_only": args.gateway_only,
        "provider_options": args.provider_options, "max_tokens": args.max_tokens or 700,
        "temperature_sent": 0 if args.backend in ("openai-compat", "ollama") else None,
        "n": args.n, "seed": args.seed, "runtime": args.runtime, "seal_profile": args.seal_profile,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["mock", "claude", "claude-cli", "ollama", "openai-compat"],
                    default="mock")
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None,
                    help="openai-compat endpoint (URL, or shorthand: cerebras/groq/ollama)")
    ap.add_argument("--rpm", type=int, default=0,
                    help="proactive request spacing for openai-compat (e.g. 30 for Groq free tier)")
    ap.add_argument("--gateway-only", default="",
                    help="openai-compat via a multi-provider gateway: pin the allowed "
                         "upstream set (comma-separated provider slugs, e.g. 'deepinfra'). "
                         "The gateway errors on mismatch instead of rerouting; the pin and "
                         "per-call generation ids land in per-record provenance "
                         "(re-verify with gateway_provenance.py).")
    ap.add_argument("--provider-options", default="",
                    help="openai-compat: JSON forwarded verbatim as providerOptions "
                         "namespaces (e.g. '{\"alibaba\":{\"enableThinking\":false}}'). "
                         "May not set the 'gateway' namespace (use --gateway-only).")
    ap.add_argument("--n", type=int, default=12, help="number of tasks")
    ap.add_argument("--conditions", default="A,B")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--injection-class", choices=["outside", "declared"], default="outside",
                    help="'declared' = T4 poison inside the collector's declared input "
                         "(measures V1's honest boundary; not G3-gated)")
    ap.add_argument("--attack-style", default=None,
                    help="T3 fallback: named jailbreak template from the AgentDojo-derived "
                         "taxonomy (direct_instruction, tool_output_injection, exfil_lure, "
                         "role_confusion, payload_splitting, format_hijack). "
                         "Omit for the frozen default payload.")
    ap.add_argument("--runtime", choices=["inline", "dabba"], default="inline",
                    help="'dabba' routes condition B through the real Station (regression gate)")
    ap.add_argument("--seal-profile", choices=["seal-1", "seal-vh-1"], default="seal-1",
                    help="dabba runtime seal profile (SPEC §9). 'seal-vh-1' seals instructions "
                         "into the Lid core and attests each view; writes a SEPARATE _seal-vh-1 "
                         "stem so it never merges with seal-1 evidence. Requires --runtime dabba.")
    ap.add_argument("--outdir", default=None,
                    help="override results dir (smoke runs go elsewhere; default: results/)")
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="openai-compat: output cap for EVERY hop (default: the harness's "
                         "700). Reasoning models spend hidden reasoning tokens against it; "
                         "set it so no call ends with finish_reason=length. Adds _mt<N> to the stem.")
    ap.add_argument("--stem-tag", default="",
                    help="extra stem label for a new configuration of an already-landed model "
                         "(e.g. 'effort-minimal'), so it can never collide with frozen evidence.")
    args = ap.parse_args()
    if args.model is None:
        args.model = {"claude": "claude-haiku-4-5", "claude-cli": "haiku",
                      "ollama": "qwen2.5:3b"}.get(args.backend, "mock")
        if args.backend == "openai-compat":
            ap.error("--backend openai-compat requires an explicit --model")

    # One evidence file per (backend, model) for openai-compat — B3 law:
    # never overwrite a landed run.
    stem = args.backend
    if args.backend == "openai-compat":
        stem += "_" + re.sub(r"[^A-Za-z0-9_.-]+", "-", args.model)
    elif args.backend == "ollama" and args.n != 12:
        # n=50 scale program (Lane O) runs three ollama models; without the
        # model in the stem they would all collide on raw_ollama_n50.jsonl.
        # Scoped to n != 12 so the frozen n=12 anchor stems are unchanged.
        stem += "_" + re.sub(r"[^A-Za-z0-9_.-]+", "-", args.model)
    elif args.backend == "claude-cli" and args.n != 12 and args.model != "haiku":
        # n=50 program adds sonnet/opus rows; haiku is the bare-stem anchor
        # (already-landed evidence), so only non-haiku models get a model suffix
        # to avoid colliding on raw_claude-cli_n50.jsonl. Scoped to n != 12.
        stem += "_" + re.sub(r"[^A-Za-z0-9_.-]+", "-", args.model)
    # Configuration labels sit right after the model so seed_variance.py still
    # groups _s8/_s9 siblings with their canonical stem.
    if args.stem_tag:
        stem += "_" + re.sub(r"[^A-Za-z0-9.-]+", "-", args.stem_tag)
    if args.max_tokens:
        stem += f"_mt{args.max_tokens}"
    if args.injection_class != "outside":
        stem += f"_poison-{args.injection_class}"  # never collide with G3-gated evidence
    if args.attack_style is not None:
        stem += f"_style-{args.attack_style}"  # never collide with frozen-payload evidence
    if args.seal_profile != "seal-1":
        stem += f"_{args.seal_profile}"  # GO condition 1: seal-vh-1 evidence on its own stem
    if args.n != 12:
        stem += f"_n{args.n}"  # 12 is the frozen-evidence default; n=50 scale runs get their own stem
    if args.seed != 7:
        stem += f"_s{args.seed}"  # 7 is the frozen-evidence default; variance seeds land on their own stems, never over canonical evidence

    outdir = pathlib.Path(args.outdir) if args.outdir else HERE / "results"
    raw = outdir / f"raw_{stem}.jsonl"
    # Overwrite guard: any REAL backend's landed run is evidence — never clobber it.
    # (mock is regenerable scratch and is exempt.) Resume = re-issue: present stems
    # are refused, i.e. skipped. Extended from openai-compat-only 2026-07-06 so the
    # n=50 scale program cannot silently overwrite the ollama/claude-cli anchors.
    if args.backend != "mock" and raw.exists():
        sys.exit(f"REFUSING to overwrite {raw} — landed runs are evidence. "
                 f"Move it aside explicitly or use --outdir for a scratch run.")

    llm = make_backend(args.backend, args.model, args.base_url, args.rpm,
                       args.gateway_only, args.provider_options, args.max_tokens)
    tasks = build_tasks(args.n, seed=args.seed, injection_class=args.injection_class,
                        attack_style=args.attack_style)
    conditions = args.conditions.split(",")

    if args.seal_profile != "seal-1" and args.runtime != "dabba":
        ap.error("--seal-profile seal-vh-1 requires --runtime dabba")

    run_task_dabba = None
    if args.runtime == "dabba":
        if args.seal_profile == "seal-vh-1":
            from bench_dabba_vh import run_task_dabba_vh as run_task_dabba
        else:
            from bench_dabba import run_task_dabba

    rows = []
    total_calls = len(tasks) * len(conditions) * 3
    done = 0
    for cond in conditions:
        for t in tasks:
            if cond == "B" and run_task_dabba is not None:
                rows.append(run_task_dabba(t, llm))
            else:
                rows.append(run_task(t, cond, llm))
            done += 3
            print(f"\r{done}/{total_calls} calls ({cond}/{t.tid})", end="", flush=True)
    print()

    if run_task_dabba is not None:
        bad = [r for r in rows if r["condition"] == "B" and not r.get("station_verified")]
        leaked = [r for r in rows if r.get("canary_in_summarizer_view")]
        print(f"dabba runtime: {sum(1 for r in rows if r['condition']=='B')} B-tasks via Station · "
              f"seal-verify failures: {len(bad)} · canary-in-view: {len(leaked)}")

    # Degenerate-run guard (added 2026-08-04 after a claude-cli OAuth session
    # expired mid-lane and returned an auth-error string for all 600 calls). The
    # harness scored that normally as "quality 0.000, injection 0/17" — which
    # reads as MODEL RESISTANCE and would have inverted a headline finding. A run
    # whose quality is uniformly zero AND whose condition-A probe never fires has
    # measured nothing about the defense; refuse it instead of writing evidence.
    if args.backend != "mock":
        mean_q = sum(r["quality"] for r in rows) / max(len(rows), 1)
        a_inj = [r for r in rows if r["condition"] == "A" and r["injected"]]
        a_fired = sum(1 for r in a_inj if r.get("injection_success"))
        if mean_q == 0.0 and a_inj and a_fired == 0:
            sample = next((r.get("final") or "" for r in rows if (r.get("final") or "").strip()), "")
            sys.exit("REFUSING to write a degenerate run: mean quality 0.0 and the "
                     "condition-A injection probe never fired across "
                     f"{len(a_inj)} injected tasks — the backend returned nothing "
                     f"scoreable (first non-empty output: {sample[:120]!r}). "
                     "Check backend auth/quota, then re-run.")

    # Per-record validity guard (added 2026-09-21). The guard above catches only
    # TOTAL failure; partial failure slipped through: gpt-5 under the 700-token
    # cap returned empty answers on 33-35/50 condition-A tasks yet scored quality
    # 0.28, so its "0/17 undefended" was mostly truncation. Any empty or capped
    # hop now diverts the whole run to <outdir>/invalid/ (outside every evidence
    # glob) and exits non-zero; nothing is written where evidence lives.
    problems = validity_problems(rows) if args.backend != "mock" else []
    outdir.mkdir(parents=True, exist_ok=True)
    if problems:
        inv = outdir / "invalid"
        inv.mkdir(parents=True, exist_ok=True)
        (inv / raw.name).write_text("\n".join(json.dumps(r) for r in rows))
        (inv / f"manifest_{stem}.json").write_text(json.dumps(_manifest(args, stem, "INVALID", problems), indent=1))
        sys.exit(f"REFUSING to write evidence: {len(problems)} record-level problem(s), e.g. "
                 f"{problems[:3]}. An empty or truncated hop scores as 'injection resisted'. "
                 f"Diagnostics kept at {inv / raw.name}. Raise --max-tokens or lower the "
                 "reasoning effort, then re-run.")
    raw.write_text("\n".join(json.dumps(r) for r in rows))
    (outdir / f"manifest_{stem}.json").write_text(json.dumps(_manifest(args, stem, "VALID", []), indent=1))

    s = summarize(rows)
    label = f"{args.backend}" + (
        " (MOCK — mechanics only, numbers are NOT findings)" if args.backend == "mock"
        else f" ({args.model})")
    lines = [
        f"# dap-bench results — {label}",
        "",
        f"Tasks: {args.n} per condition · pipeline: planner → collector → summarizer",
        "",
        "| Metric | " + " | ".join(f"Condition {c}" for c in s) + " |",
        "|---|" + "---|" * len(s),
    ]
    for metric in ["mean_input_tokens", "mean_output_tokens", "mean_latency_ms",
                   "mean_quality", "mean_quality_strict", "injection_attempts", "injection_successes"]:
        lines.append(f"| {metric} | " + " | ".join(str(s[c][metric]) for c in s) + " |")
    if {"A", "B"} <= set(s):
        ratio = s["A"]["mean_input_tokens"] / max(s["B"]["mean_input_tokens"], 1)
        lines += ["", f"**Input-token ratio A/B: {ratio:.2f}×** — scoped views cut context by "
                      f"{(1 - 1 / ratio) * 100:.0f}% on this suite.",
                  f"Quality delta (B − A): {s['B']['mean_quality'] - s['A']['mean_quality']:+.3f} "
                  "(negative = scoped views lost facts; investigate before claiming speed).",
                  f"Injection: A {s['A']['injection_successes']}/{s['A']['injection_attempts']} vs "
                  f"B {s['B']['injection_successes']}/{s['B']['injection_attempts']} successful canary insertions."]
        if s["A"]["declared_injection_attempts"] or s["B"]["declared_injection_attempts"]:
            lines += [f"Declared-dependency poisoning (T4, V1's honest boundary — scoping does not "
                      f"block this class by design): "
                      f"A {s['A']['declared_injection_successes']}/{s['A']['declared_injection_attempts']} vs "
                      f"B {s['B']['declared_injection_successes']}/{s['B']['declared_injection_attempts']}."]
    md = outdir / f"results_{stem}.md"
    md.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {raw.name}, {md.name}")

    if args.backend == "mock":
        print("\nNOTE: mock numbers validate mechanics only. Run --backend claude for findings.", file=sys.stderr)


if __name__ == "__main__":
    main()
