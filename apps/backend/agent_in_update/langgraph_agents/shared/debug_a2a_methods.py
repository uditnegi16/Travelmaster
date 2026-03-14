# debug_a2a_methods.py
import importlib, inspect, json, os, sys

print("Python:", sys.version)
try:
    mod_path = importlib.util.find_spec("a2a").origin
    print("a2a package path:", mod_path)
except Exception as e:
    print("Could not find 'a2a' package via importlib:", e)

try:
    mod = importlib.import_module("a2a.server.apps.jsonrpc.jsonrpc_app")
    print("Imported module:", mod.__name__)
except Exception as e:
    print("Failed to import a2a.server.apps.jsonrpc.jsonrpc_app:", e)
    # Also print top-level a2a server apps
    try:
        apps_mod = importlib.import_module("a2a.server.apps")
        print("a2a.server.apps found:", apps_mod)
    except Exception as e2:
        print("Also failed to import a2a.server.apps:", e2)
    raise SystemExit(1)

# Print module members
members = {name: type(getattr(mod, name)).__name__ for name in dir(mod) if not name.startswith("__")}
print("\nModule members (sample):")
for name, t in list(members.items())[:80]:
    print(" ", name, t)

# Try to find classes or dicts with 'methods' or 'registry'
candidates = []
for name in dir(mod):
    obj = getattr(mod, name)
    try:
        if hasattr(obj, "methods") or hasattr(obj, "method_map") or hasattr(obj, "dispatch") or hasattr(obj, "register"):
            candidates.append((name, obj))
    except Exception:
        pass

print("\nDiscovery candidates (objects with likely RPC attrs):")
for name, obj in candidates:
    print(" -", name, "->", type(obj))
    try:
        print("   attrs:", [a for a in dir(obj) if "method" in a or "register" in a][:20])
    except Exception:
        pass

# If any class looks promising, inspect its source
for name, obj in candidates:
    try:
        src = inspect.getsource(obj)
        print(f"\n--- Source of {name} (first 400 chars) ---")
        print(src[:400])
    except Exception as e:
        print(f"Could not get source for {name}: {e}")

# Also search a2a package files directly for common RPC method names
root = os.path.dirname(mod.__file__)
print("\nLooking for strings in package files under:", root)
strings_to_search = ["sendMessage", "getTask", "a2a.", "task.get", "send", "message", "method.not"]
found = {}
for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith(".py"):
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    txt = f.read()
                for s in strings_to_search:
                    if s in txt:
                        found.setdefault(s, []).append(fp)
            except Exception:
                pass

print("\nSearch hits for common strings:")
print(json.dumps({k: len(v) for k, v in found.items()}, indent=2))
for k, paths in found.items():
    print(f"\n== {k} -> {len(paths)} files ==")
    for p in paths[:10]:
        print("  ", p)
