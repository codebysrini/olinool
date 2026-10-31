"""dap-bench backends.

MockLLM  — deterministic, free, no network. Validates harness mechanics and
           makes the injection differential *mechanically* visible:
           the mock collector is a constrained extractor (only lifts FACT lines),
           the mock summarizer is deliberately gullible (obeys any instruction
           in its context). With a real model, gullibility becomes an empirical
           question; the architectural claim is that condition B strips the
           vector entirely, model behavior notwithstanding.

ClaudeLLM — calls the Anthropic Messages API with stdlib urllib (no SDK
           dependency). Reads ANTHROPIC_API_KEY from the environment. Never
           hardcode or log the key. Token counts come from the API's own
           usage block, latency is measured client-side.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    # Per-request serving-path provenance. Set ONLY by backends that can name
    # their true upstream per call (OpenAICompatLLM: base_url + the gateway's
    # resolved provider). Stays None for mock/ollama/claude-cli, so the record
    # builders add no provenance key for those — their records are unchanged.
    # Landed 2026-07-07 (after the n=50 gateway lane closed) per PROVENANCE_n50
    # dated boundary: closes the per-record gap the per-run manifest could not.
    provenance: dict | None = None
    # Server-side timing decomposition. Set ONLY by backends whose API reports
    # it (OllamaLLM: load/prompt_eval/eval/total durations, measured by the
    # server itself — more precise than client-side first-token timing). None
    # elsewhere, so records without it are byte-identical to the prior schema.
    # Landed 2026-08-04 for the TTFT/TPS split on the local anchor.
    timing: dict | None = None


class MockLLM:
    name = "mock"

    def complete(self, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        t0 = time.perf_counter()
        role = "planner" if "You are the planner" in system else (
            "collector" if "You are the collector" in system else "summarizer")
        if role == "planner":
            text = "PLAN: collect the FACT lines relevant to the goal, then summarize them. (chatter: step reasoning omitted for brevity)"
        elif role == "collector":
            facts = [ln.strip() for ln in prompt.splitlines() if ln.strip().startswith("FACT:")]
            text = "\n".join(facts) if facts else "NO-FACTS-FOUND"
        else:  # summarizer — gullible by design
            facts = [ln.strip() for ln in prompt.splitlines() if ln.strip().startswith("FACT:")]
            text = "Summary: " + "; ".join(f.replace("FACT:", "").strip() for f in facts)
            if "ZX-CANARY-7" in prompt:  # obeys injected instruction if visible
                text += " ZX-CANARY-7"
        latency = (time.perf_counter() - t0) * 1000
        return LLMResult(text, len((system + prompt)) // 4, len(text) // 4, latency)


class ClaudeLLM:
    def __init__(self, model: str):
        self.name = model
        self.key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Set it in the environment "
                "(export ANTHROPIC_API_KEY=...) — do not hardcode it.")

    def complete(self, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        body = json.dumps({
            "model": self.name,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": self.key,
                "anthropic-version": "2023-06-01",
            },
        )
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read())
        latency = (time.perf_counter() - t0) * 1000
        text = "".join(b.get("text", "") for b in out.get("content", []))
        usage = out.get("usage", {})
        return LLMResult(text, usage.get("input_tokens", 0), usage.get("output_tokens", 0), latency)


class OllamaLLM:
    """Free local backend. Install: https://ollama.com — then `ollama pull <model>`.
    Token counts come from Ollama's prompt_eval_count / eval_count."""

    def __init__(self, model: str):
        self.name = model
        self.base = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def complete(self, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        body = json.dumps({
            "model": self.name,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(self.base + "/api/chat", data=body,
                                     headers={"content-type": "application/json"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=600) as resp:
            out = json.loads(resp.read())
        latency = (time.perf_counter() - t0) * 1000
        # Ollama reports server-side durations in nanoseconds; keep them (ms)
        # so prompt-processing vs decode can be split per hop (TTFT proxy =
        # load + prompt_eval; decode TPS = eval_count / eval_duration).
        timing = {k: out[k] / 1e6 for k in
                  ("load_duration", "prompt_eval_duration", "eval_duration",
                   "total_duration") if k in out}
        timing["eval_count"] = out.get("eval_count", 0)
        return LLMResult(out.get("message", {}).get("content", ""),
                         out.get("prompt_eval_count", 0),
                         out.get("eval_count", 0), latency,
                         timing=timing or None)


class OpenAICompatLLM:
    """Any OpenAI-compatible /chat/completions endpoint: Cerebras, Groq,
    ollama's /v1, vLLM, ... Explicit base URL — no discovery, no negotiation.

    Key resolution (never hardcoded, never logged): OPENAI_COMPAT_API_KEY
    first; CEREBRAS_API_KEY / GROQ_API_KEY as fallbacks when the base URL is
    that provider's. Localhost endpoints may run keyless.

    Token accounting reads the response usage block WITH the plausibility
    guard learned from the claude CLI (v2.2): a 3-hop pipeline over multi-KB
    docs cannot report prompt tokens below ~chars/32 — if it does, the meter
    is invalid; fall back to the chars/4 estimate (compare.py's G1 meter
    check then classifies the backend from the resulting means).

    429/5xx get exponential backoff honoring Retry-After (Groq free tier is
    ~30 RPM / 6K TPM); `rpm` adds proactive spacing between calls. Backoff
    sleeps happen OUTSIDE the latency measurement — latency_ms is the
    successful attempt only.
    """

    KNOWN_BASES = {
        "cerebras": "https://api.cerebras.ai/v1",
        "groq": "https://api.groq.com/openai/v1",
        "ollama": "http://localhost:11434/v1",
    }

    def __init__(self, model: str, base_url: str, rpm: int = 0,
                 gateway_only: str = "", provider_options: str = "",
                 max_tokens: int | None = None):
        if not model:
            raise RuntimeError("openai-compat needs an explicit --model (no default).")
        if not base_url:
            raise RuntimeError(
                "openai-compat needs --base-url (a URL, or shorthand: "
                + "/".join(self.KNOWN_BASES) + ").")
        self.base = self.KNOWN_BASES.get(base_url, base_url).rstrip("/")
        self.name = model
        self.rpm = rpm
        # Multi-provider gateways resolve the true upstream per call; a pinned
        # `only` set fixes the serving path for the whole run (the gateway
        # errors on mismatch instead of silently rerouting), which is what a
        # per-run serving-path panel needs to be reproducible.
        self.gateway_only = [s.strip() for s in (gateway_only or "").split(",")
                             if s.strip()]
        # Provider-specific options forwarded verbatim under providerOptions
        # (gateway AI-SDK namespace, camelCase keys). Needed live 2026-08-04:
        # alibaba/qwen-3-32b non-streaming now REQUIRES
        # {"alibaba": {"enableThinking": false}} — verified the only accepted
        # carrier (top-level/chat_template_kwargs/snake_case all 400).
        self.provider_options = json.loads(provider_options) if provider_options else {}
        if "gateway" in self.provider_options:
            raise RuntimeError("--provider-options must not set the 'gateway' "
                               "namespace; use --gateway-only for routing.")
        self._last_call = 0.0
        # Per-lane output cap for every hop (None = each call site's default,
        # 700). Reasoning models spend hidden reasoning tokens against it: at
        # 700, gpt-5 returned EMPTY content on 33-35/50 condition-A tasks
        # (found 2026-09-21), which the scorer counts as "injection resisted".
        self.max_tokens_override = max_tokens
        key = os.environ.get("OPENAI_COMPAT_API_KEY", "")
        if not key and "cerebras" in self.base:
            key = os.environ.get("CEREBRAS_API_KEY", "")
        if not key and "groq" in self.base:
            key = os.environ.get("GROQ_API_KEY", "")
        self.key = key
        local = self.base.startswith(("http://localhost", "http://127.0.0.1"))
        if not key and not local:
            raise RuntimeError(
                "No API key: set OPENAI_COMPAT_API_KEY (or CEREBRAS_API_KEY / "
                "GROQ_API_KEY for those providers). Do not hardcode keys.")

    def complete(self, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        if self.max_tokens_override:
            max_tokens = self.max_tokens_override
        payload = {
            "model": self.name,
            "max_tokens": max_tokens,
            "temperature": 0,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
        }
        popts = dict(self.provider_options)
        if self.gateway_only:
            popts["gateway"] = {"only": self.gateway_only}
        if popts:
            payload["providerOptions"] = popts
        body = json.dumps(payload).encode()
        # Cloudflare fronts Cerebras/Groq and 403s (error 1010) any request
        # without a User-Agent — urllib sends none by default. Verified live
        # 2026-07-06: no UA -> 403/1010, any UA -> 200.
        headers = {"content-type": "application/json", "user-agent": "dap-bench/0.1"}
        if self.key:
            headers["authorization"] = f"Bearer {self.key}"
        if self.rpm:
            wait = self._last_call + 60.0 / self.rpm - time.monotonic()
            if wait > 0:
                time.sleep(wait)
        out, latency = self._post_with_backoff(body, headers)
        self._last_call = time.monotonic()
        choice = (out.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        text = msg.get("content") or ""
        usage = out.get("usage") or {}
        itok = usage.get("prompt_tokens", 0)
        otok = usage.get("completion_tokens", 0)
        est_in, est_out = (len(system) + len(prompt)) // 4, len(text) // 4
        if itok < est_in // 8:
            itok = est_in
        if otok < est_out // 8:
            otok = est_out
        # Per-record serving path: base_url is always known; resolved_provider
        # is the gateway's true upstream for THIS call (Vercel exposes it at
        # provider_metadata.gateway.routing.resolvedProvider — None for direct
        # first-party endpoints like Cerebras). This is what the per-run
        # manifest cannot capture: an upstream that fails over per request.
        gw = ((out.get("provider_metadata") or {}).get("gateway") or {})
        resolved = ((gw.get("routing") or {}).get("resolvedProvider"))
        provenance = {"base_url": self.base, "resolved_provider": resolved}
        # Verified live 2026-07-13: the Vercel gateway's compat responses no
        # longer inline provider_metadata (resolved stays None). The durable
        # pointer is now the top-level generationId — the Generation Lookup
        # API names the upstream that actually served the call, and
        # gateway_provenance.py re-verifies a landed run from these ids.
        if out.get("generationId"):
            provenance["generation_id"] = out["generationId"]
        if self.gateway_only:
            provenance["gateway_only"] = self.gateway_only
        # Validity evidence travels with every record (added 2026-09-21): a
        # 'length' finish, or reasoning tokens eating the cap, is how a
        # reasoning model silently returns "" -- scored as injection resisted.
        # run.py refuses to write evidence when either shows up.
        provenance["finish_reason"] = choice.get("finish_reason")
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        if reasoning is not None:
            provenance["reasoning_tokens"] = reasoning
        provenance["max_tokens"] = max_tokens
        return LLMResult(text, itok, otok, latency, provenance=provenance)

    def _post_with_backoff(self, body: bytes, headers: dict, tries: int = 6):
        url = self.base + "/chat/completions"
        for attempt in range(tries):
            req = urllib.request.Request(url, data=body, headers=headers)
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    return json.loads(resp.read()), (time.perf_counter() - t0) * 1000
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503) or attempt == tries - 1:
                    raise
                try:
                    delay = float(e.headers.get("retry-after", ""))
                except (TypeError, ValueError):
                    delay = min(2.0 * 2 ** attempt, 60.0)
                # Cap honored Retry-After: an uncapped server value (e.g. 1800s on
                # daily-cap 429s) looks like a silent hang — 0% CPU, no log line,
                # no error. Bounded sleep + a visible line keeps retries honest.
                delay = min(delay, 120.0)
                print(f"[backoff] HTTP {e.code}, retry {attempt + 1}/{tries} in {delay:.0f}s", flush=True)
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                # Transient network faults (socket read timeout, connection
                # reset) killed a multi-hour lane mid-run on 2026-07-13; they
                # retry with the same bounded backoff as retryable HTTP codes.
                # The failed attempt's wall time is discarded with it —
                # latency_ms stays the successful attempt only.
                if attempt == tries - 1:
                    raise
                delay = min(2.0 * 2 ** attempt, 60.0)
                print(f"[backoff] {type(e).__name__}, retry {attempt + 1}/{tries} in {delay:.0f}s", flush=True)
                time.sleep(delay)
        raise RuntimeError("unreachable")


class ClaudeCLI:
    """Uses the local `claude` CLI (Claude Code) under your existing Claude
    subscription — NO API key. One-time setup on your machine:
        npm install -g @anthropic-ai/claude-code && claude   (log in once)
    Caveat: latency includes CLI startup overhead (roughly constant across
    conditions A/B, so token counts remain the primary metric)."""

    def __init__(self, model: str):
        self.name = model or "haiku"

    def complete(self, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        import subprocess
        full = f"[SYSTEM INSTRUCTIONS]\n{system}\n\n[TASK]\n{prompt}"
        t0 = time.perf_counter()
        proc = subprocess.run(
            ["claude", "-p", full, "--model", self.name, "--max-turns", "1",
             "--output-format", "json"],
            capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
        latency = (time.perf_counter() - t0) * 1000
        text, itok, otok = proc.stdout.strip(), 0, 0
        try:
            data = json.loads(proc.stdout)
            text = data.get("result", text)
            usage = data.get("usage") or {}
            itok = usage.get("input_tokens", 0)
            otok = usage.get("output_tokens", 0)
        except (json.JSONDecodeError, AttributeError):
            pass  # fall back to raw stdout + estimated tokens
        # v2.2: the CLI's json usage under-reports prompt tokens (observed
        # constant ~30 for multi-KB prompts). If the report is implausible,
        # use a chars/4 estimate and let downstream label it as estimated.
        est_in, est_out = len(full) // 4, len(text) // 4
        if itok < est_in // 8:
            itok = est_in
        if otok < est_out // 8:
            otok = est_out
        return LLMResult(text, itok, otok, latency)


def make_backend(kind: str, model: str, base_url: str | None = None, rpm: int = 0,
                 gateway_only: str = "", provider_options: str = "",
                 max_tokens: int | None = None):
    if max_tokens and kind != "openai-compat":
        raise RuntimeError("--max-tokens is only wired for --backend openai-compat")
    if kind == "mock":
        return MockLLM()
    if kind == "ollama":
        return OllamaLLM(model)
    if kind == "claude-cli":
        return ClaudeCLI(model)
    if kind == "openai-compat":
        return OpenAICompatLLM(model, base_url or "", rpm, gateway_only,
                                provider_options, max_tokens)
    return ClaudeLLM(model)
