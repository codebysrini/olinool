# Independent reproduction ledger

Fill this in after `./reproduce.sh` completes and send it back with your
`repro_out_*/raw_ollama.jsonl`. One block per reproduction. This mirrors the
provenance discipline of this benchmark's own evidence: every number traces to a run.

---

## Reproduction record

- **Reproducer:** <name or handle; may be withheld — see note below>
- **Affiliation (optional):**
- **Date (UTC):**
- **Repo commit reproduced (`git rev-parse HEAD`):**

### Environment
- **OS / arch:**
- **Python:** (`python3.12 --version`)
- **ollama version:** (`ollama --version`)
- **Anchor model + digest:** (`ollama list | grep qwen2.5:3b`)

### Result (paste the `reproduce_check.py` output verbatim)

```
<paste the PASS/FAIL block and the reference-vs-yours table here>
```

### Verdict
- [ ] REPRODUCED (exit 0)
- [ ] DIVERGENCE (exit 1 — please describe below; a genuine divergence is a finding)

### Notes / anomalies (optional)
<anything surprising: which check drifted, how far, any environment quirk>

### Optional extended reproduction (needs your own provider key — has cost)
- [ ] Multi-model economics (which provider / models):
- [ ] AgentDojo same-benchmark cost / attack families:
- Numbers observed:

---

**On attribution & anonymity.** Independent reproductions are acknowledged in
this project's release notes and in research writing that builds on the
benchmark — either by name or generically ("N independent parties reproduced
the anchor result"), at your preference. Where a publication process restricts
naming individuals, attribution is added in the final public version:

- [ ] Name me in public acknowledgments
- [ ] Keep me anonymous throughout
