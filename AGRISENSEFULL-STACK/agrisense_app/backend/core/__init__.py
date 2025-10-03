"""agrisense_app.backend.core
---------------------------------
Core utilities for the AgriSense backend.

Avoid importing submodules at package import time to prevent circular
import issues when `agrisense_app.backend.main` performs flexible
import resolution. Submodules (for example ``et0``) should be imported
explicitly where needed.
"""

__all__ = []
__version__ = "1.0.0"