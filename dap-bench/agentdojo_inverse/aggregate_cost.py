"""Aggregate the multi-seed cost matrix into a per-(model,suite) table with
variance, and list missing cells (429-failed) for a gap-fill pass. Reads all
results/inverse_*_cost_s*.json. Same-benchmark cost is the review-C2 fix; the
per-seed spread is the review-C3 fix. No network.
"""
import glob
import json
import statistics as st
from collections import defaultdict

MODELS = ["gpt-oss-120b", "gemma-4-31b"]
SUITES = ["banking", "slack", "travel", "workspace"]
SEEDS = [1, 2, 3]
ARMS = ["undefended", "scoped-collector", "structural"]

cells = defaultdict(dict)  # (model,suite) -> {seed: summary}
for f in sorted(glob.glob("results/inverse_cerebras_*_cost_s*.json")):
    d = json.load(open(f))
    m, su, tag = d["meta"]["model"], d["meta"]["suite"], d["meta"]["tag"]
    seed = int(tag.split("_s")[-1])
    cells[(m, su)][seed] = d["summary"]


def vals(model, suite, arm, key):
    out = []
    for seed in SEEDS:
        s = cells.get((model, suite), {}).get(seed)
        if s and s.get(arm, {}).get(key) is not None:
            out.append(s[arm][key])
    return out


def mean_rng(xs):
    if not xs:
        return "--"
    if len(xs) == 1:
        return f"{xs[0]:.2f}"
    return f"{st.mean(xs):.2f} [{min(xs):.2f},{max(xs):.2f}]"


missing = [(m, su, seed) for m in MODELS for su in SUITES for seed in SEEDS
           if seed not in cells.get((m, su), {})]

print("=== same-benchmark token cost vs undefended (mean [min,max] over seeds) ===")
print(f"{'model':13} {'suite':10} {'collector':>18} {'structural':>18}")
for m in MODELS:
    for su in SUITES:
        c = mean_rng(vals(m, su, "scoped-collector", "tok_vs_undef"))
        s = mean_rng(vals(m, su, "structural", "tok_vs_undef"))
        print(f"{m:13} {su:10} {c:>18} {s:>18}")

# attack-success rate with variance (as fraction) — the C3 fix
def att(model, suite, arm):
    fr = []
    for seed in SEEDS:
        s = cells.get((model, suite), {}).get(seed)
        if s and arm in s:
            a = s[arm]["attack_success"]
            n, d = a.split("/")
            fr.append(int(n) / int(d))
    return fr

print("\n=== attack success rate (mean over seeds), per arm ===")
print(f"{'model':13} {'suite':10} {'undef':>8} {'collector':>10} {'structural':>11}")
for m in MODELS:
    for su in SUITES:
        u = att(m, su, "undefended"); c = att(m, su, "scoped-collector"); s = att(m, su, "structural")
        f = lambda x: f"{st.mean(x):.2f}" if x else "--"
        print(f"{m:13} {su:10} {f(u):>8} {f(c):>10} {f(s):>11}")

# aggregate cost across all cells present
allc = [v for m in MODELS for su in SUITES for v in vals(m, su, "scoped-collector", "tok_vs_undef")]
alls = [v for m in MODELS for su in SUITES for v in vals(m, su, "structural", "tok_vs_undef")]
print(f"\nAGG collector tok_vs_undef: mean {st.mean(allc):.2f} range [{min(allc):.2f},{max(allc):.2f}] n={len(allc)}"
      if allc else "AGG collector: none")
print(f"AGG structural tok_vs_undef: mean {st.mean(alls):.2f} range [{min(alls):.2f},{max(alls):.2f}] n={len(alls)}"
      if alls else "AGG structural: none")
print(f"\ncells present: {sum(len(v) for v in cells.values())}/24  missing (429-failed): {missing}")
