"""dabba — portable task-state with scoped views (DAP v0.1).

A task travels as a Dabba (lunchbox): a Lid (header), append-only Tiers
(agent outputs), and a hash-linked Seal chain (tamper-evidence). Each hop
receives only its scoped working view W(k) — the property benchmarked in
dap-bench: cheaper, faster, and injection-resistant by construction.

Crypto is the shared `moolam` package. dabba runs standalone; if `olinool`
is also installed, `dabba.bridge` cross-links authority (receipts) with
action (sealed tiers). See SPEC.md.

    pip install dabba          # standalone task state / scoped views
    pip install dabba olinool  # + governance bridge
"""
from .model import PROFILE_SEAL_1, PROFILE_SEAL_VH_1, Dabba, Lid, Tier  # noqa: F401
from .station import Station, Verdict, audit_view_no_leak  # noqa: F401
from .views import WorkingView, build_view  # noqa: F401

__version__ = "0.2.0"

# Optional governance bridge — loads only if olinool is present.
try:  # pragma: no cover - exercised in bridge tests
    import olinool  # noqa: F401

    from . import bridge  # noqa: F401
    HAS_OLINOOL = True
except ImportError:  # pragma: no cover
    HAS_OLINOOL = False
