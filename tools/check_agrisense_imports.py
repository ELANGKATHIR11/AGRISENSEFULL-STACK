"""Helper: print which `agrisense_app` package is resolved on import.

Run this from the repository root to see which filesystem path Python will import
for the `agrisense_app` package. This can help when consolidating duplicates.
"""
import importlib
import inspect
import sys


def main():
    try:
        mod = importlib.import_module('agrisense_app')
    except Exception as e:
        print('agrisense_app import failed:', e)
        sys.exit(1)

    print('agrisense_app module:', mod)
    print('file:', getattr(mod, '__file__', None))
    print('package path entries:')
    for p in getattr(mod, '__path__', []):
        print('  -', p)


if __name__ == '__main__':
    main()
