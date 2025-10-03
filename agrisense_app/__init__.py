"""Namespace package shim for agrisense_app.

This file makes the top-level `agrisense_app` directory a package and extends
its __path__ to include the `AGRISENSEFULL-STACK/agrisense_app` copy so imports
like `import agrisense_app.backend.core` resolve to the comprehensive package
used by tests.
"""
import os
import pkgutil

# Insert the alternate package path (AGRISENSEFULL-STACK/agrisense_app) if it exists
base = os.path.dirname(__file__)
alt = os.path.join(os.path.dirname(base), 'AGRISENSEFULL-STACK', 'agrisense_app')
if os.path.isdir(alt):
    __path__.append(alt)  # type: ignore

# Allow pkgutil-style namespace packages if needed
__all__ = [name for _, name, _ in pkgutil.iter_modules(__path__)]
