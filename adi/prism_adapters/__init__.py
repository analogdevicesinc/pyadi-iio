"""ADI-specific Prism plugin adapters: IQ analyzer + DUT capture session hook."""

from adi.prism_adapters.iq import IQRenderer

# ADIDUTHook lands in Task 20 — guard the import so __init__ doesn't fail
# during the gap between Task 18 and Task 20 commits.
try:
    from adi.prism_adapters.capture import ADIDUTHook
    __all__ = ["IQRenderer", "ADIDUTHook"]
except ImportError:
    __all__ = ["IQRenderer"]
