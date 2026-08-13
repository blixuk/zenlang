import os

def zen_trace(message: str):
    """Optional file-based tracer. Enable with ZEN_TRACE=1 (or any non-empty/non-0 value)."""
    flag = os.environ.get("ZEN_TRACE", "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return
    try:
        with open("ZEN_DEBUG.log", "a") as f:
            f.write(f"{message}\n")
    except Exception:
        pass
