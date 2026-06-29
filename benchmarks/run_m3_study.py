"""M3 powered live study driver (AP-0050).

Runs the non-batchable chain recovery study live against several OpenAI-compatible providers with
more repetitions and both crash points than M2, recording a manifest + replayable transcript per
target. Each target is isolated: a provider that rate-limits or 404s is recorded and skipped, never
aborting the others. Keys are read from the environment only (loaded from a gitignored `.env` here),
never printed or committed.

Usage:
    python benchmarks/run_m3_study.py            # all configured targets
    python benchmarks/run_m3_study.py groq       # only targets whose provider matches an arg
"""

try:
    import _bootstrap  # noqa: F401  (sys.path + UTF-8 stdout when run as a script)
except ModuleNotFoundError:
    pass

import os
import sys
import traceback

from benchmarks.live_study import run_live_study


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader: KEY=value lines into os.environ (existing env wins). No printing."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip("'").strip('"')
            os.environ.setdefault(key, val)


# (provider, model, key_env, repeats). Models chosen to be instruction/code reliable on each free
# tier; provider is pure config (ADR-0010). Groq is fast with higher free limits → more repeats for
# the powered signal; OpenRouter's free Nemotron is rate-limited → fewer (M2 hit 429 at higher n).
TARGETS = [
    ("groq", "llama-3.3-70b-versatile", "GROQ_API_KEY", 8),
    ("groq", "openai/gpt-oss-120b", "GROQ_API_KEY", 8),
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free", "OPENROUTER_API", 3),
    ("zenmux", "openai/gpt-4o-mini", "ZENMUX_API", 3),
]

# Powered relative to M2 (n=2): up to 8 repetitions, both crash points, on a length-6 chain.
N = 6
STEPS = (2, 3)
MAX_CALLS = 1200


def main() -> None:
    _load_dotenv()
    wanted = set(sys.argv[1:])
    results = []
    for provider, model, key_env, repeats in TARGETS:
        if wanted and provider not in wanted:
            continue
        if not os.environ.get(key_env):
            print(f"\n[skip] {provider}:{model} — ${key_env} not set in environment")
            results.append((provider, model, "no-key", None))
            continue
        print("\n" + "=" * 100)
        print(f"TARGET provider={provider} model={model} repeats={repeats}")
        print("=" * 100)
        try:
            verdict = run_live_study(
                model, provider=provider, api_key_env=key_env,
                n=N, steps=STEPS, repeats=repeats, max_calls=MAX_CALLS,
            )
            results.append((provider, model, "ok", verdict.get("supported")))
        except Exception as exc:  # one target's failure must not sink the rest (honest record)
            print(f"\n[!] {provider}:{model} FAILED: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            results.append((provider, model, f"error:{type(exc).__name__}", None))

    print("\n\n" + "#" * 100)
    print("M3 POWERED STUDY — SUMMARY")
    print("#" * 100)
    for provider, model, status, supported in results:
        sup = "" if supported is None else f" | C1 supported={supported}"
        print(f"  {provider:>10} | {model:<42} | {status}{sup}")
    print("\nHonest scope (ADR-0009): free-tier models, small n; a SUPPORTED verdict here is the first")
    print("powered live signal, not the final word. Negatives recorded, not buried.")


if __name__ == "__main__":
    main()
