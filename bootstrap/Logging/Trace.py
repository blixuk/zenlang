import os

def zen_trace(message: str):
    """Global file-based tracer to avoid stream redirection issues in build system."""
    try:
        with open("ZEN_DEBUG.log", "a") as f:
            f.write(f"{message}\n")
    except:
        pass
