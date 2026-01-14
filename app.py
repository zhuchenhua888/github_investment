# -*- coding: utf-8 -*-
"""
Compatibility entrypoint for Vercel / external WSGI loaders.

This file locates and executes the project's actual Flask app file
located at `韭菜助手_web/app.py` and exposes a top-level `app` object.

Vercel looks for a top-level `app` variable in one of several named files
(app.py, index.py, main.py, ...). Because this project keeps the Flask
app inside a subfolder with a non-ASCII name, we execute that file and
re-export its `app` (or `create_app()`) so the platform can find it.

This approach avoids renaming directories or changing the existing
application code.
"""
from __future__ import annotations

import os
import runpy
from typing import Any

ROOT = os.path.dirname(__file__)
TARGET_SUBDIR = os.path.join(ROOT, "韭菜助手_web")
TARGET_FILE = os.path.join(TARGET_SUBDIR, "app.py")

if not os.path.exists(TARGET_FILE):
    raise FileNotFoundError(f"Expected application file at: {TARGET_FILE}")

# Execute the target app.py in an isolated namespace and obtain the
# Flask application object. This will run top-level definitions but will
# not trigger a guarded `if __name__ == '__main__'` block (that only
# runs when executed as a script).
ns: dict[str, Any] = runpy.run_path(TARGET_FILE)

# Common patterns: `app` (Flask instance) or `create_app()` factory.
if "app" in ns and ns["app"] is not None:
    app = ns["app"]
elif "create_app" in ns and callable(ns["create_app"]):
    app = ns["create_app"]()
else:
    raise RuntimeError(
        "Could not find a Flask `app` instance or `create_app()` in "
        f"{TARGET_FILE}. Please export `app` or provide `create_app()`.")

# Export for WSGI loaders — keep name `app`.
