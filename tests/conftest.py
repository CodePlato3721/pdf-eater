"""
Conftest loaded by pytest before any test modules. Ensures backend/ takes
precedence over root core/ in sys.path, so `import core` resolves to
backend/core/ throughout the test session.
"""
import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Remove root from sys.path so root core/ cannot shadow backend core/
for _path in [ROOT_DIR, "", "."]:
    while _path in sys.path:
        sys.path.remove(_path)

# Put backend/ at position 0
while BACKEND_DIR in sys.path:
    sys.path.remove(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

# Re-add root AFTER backend so other root-level imports still work
sys.path.append(ROOT_DIR)

# Purge any stale core imports that may have been cached before this runs
for _key in list(sys.modules.keys()):
    if _key == "core" or _key.startswith("core."):
        del sys.modules[_key]
