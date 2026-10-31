# Same-harness defense baselines — independent verification, 2026-08-05

**Why:** the review panel's third converged finding was that Figure 1 compared
our measured multipliers against competitors' self-reported ones, obtained on
different models and harnesses — the exact cross-paper comparison the paper's
own introduction criticises.

**What:** a parallel session had already built the multi-defense arms and run a
matrix (`*_matrixB1.*`, 2026-07-12). Under the two-context rule, in-flight
numbers are not used in public claims until independently reproduced, so this
is a fresh run of the identical config under a separate stem
(`*_verify_2026-08-05.*`): gpt-oss-120b / banking / `important_instructions_no_names`
/ 5x8 = 40 combos. The `datafilter` arm is excluded (needs a separately-served
local 8B model).

## Cross-run comparison

| Defense | Their atk | Mine atk | Their x | Mine x | Their util | Mine util |
|---|---|---|---|---|---|---|
| undefended | 25/40 | 24/40 | 1.00 | 1.00 | 21/40 | 13/40 |
| spotlighting | 17/40 | 19/40 | 0.87 | 1.01 | 9/40 | 17/40 |
| sandwiching | 25/40 | 23/40 | 1.14 | 1.06 | 16/40 | 13/40 |
| structural (ours) | 6/40 | 8/40 | 0.82 | 0.82 | 12/40 | 18/40 |
| typed (ours) | 1/40 | 0/40 | 0.53 | 0.57 | 13/40 | 12/40 |
| scoped-collector (ours) | **0/40** | **0/40** | 0.87 | 0.84 | 17/40 | 11/40 |
| detector | 0/40 | 0/40 | 0.95 | 1.06 | **0/40** | **0/40** |
| SecInfer | 8/40 | 11/40 | 4.84 | 4.43 | 22/40 | 18/40 |

## What replicates (load-bearing)

- **Security ordering, exactly.** Weak: sandwiching (23-25) ~ undefended
  (24-25) > spotlighting (17-19). Strong: structural (6-8) > typed (0-1) =
  scoped-collector (0) = detector (0). Middle: SecInfer (8-11).
- **Cost multipliers**, within 0.05x-0.4x: structural 0.82/0.82 (exact),
  typed 0.53/0.57, scoped-collector 0.87/0.84, SecInfer 4.84/4.43.
- **The detector pathology, exactly**: 0/40 attacks AND 0/40 utility in both
  runs. It "blocks everything" by refusing to let the agent work at all.
- **The headline contrast**: subtractive arms block completely at or below
  undefended cost; inference-time scaling costs ~4.4-4.8x and still leaks.

## What does NOT replicate

**Utility counts swing widely** (undefended 21 vs 13; spotlighting 9 vs 17;
structural 12 vs 18; scoped-collector 17 vs 11). AgentDojo exposes no seed
control for these runs, so this is genuine run-to-run variance in a stochastic
pipeline, not a discrepancy between the two sessions' methods. **Consequence
for the paper: security and cost orderings are reported as findings; utility
deltas from this matrix are NOT used as load-bearing claims.** Both runs are
committed so a reader can see the spread.

## Provenance

Mine: `results/inverse_cerebras_gpt-oss-120b_banking_important_instructions_no_names_2026-08-05_verify_2026-08-05.{json,md}`.
Theirs: `*_2026-07-12_matrixB1.*` (parallel session, committed separately by them).
Paper: Figure 1 is now entirely measured bars from the verification run.
