import sys
import importlib

print("Python:", sys.version)
for name in ["pandas", "numpy", "sklearn", "rank_bm25"]:
    try:
        mod = importlib.import_module(name)
        print(name, "OK", getattr(mod, "__version__", "version unavailable"))
    except Exception as exc:
        print(name, "FAILED:", repr(exc))
        raise
print("Environment import check passed. This does not verify dataset correctness.")
