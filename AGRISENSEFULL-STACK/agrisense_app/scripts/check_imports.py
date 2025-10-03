import importlib
import traceback

modules = [
    'pytest',
    'backend.core.engine',
    'agrisense_app.backend.core.engine',
    'agrisense_app.backend.main',
]

for m in modules:
    print('\n--- trying', m)
    try:
        mod = importlib.import_module(m)
        print('OK:', m, '->', getattr(mod, '__file__', repr(mod)))
    except Exception as e:
        print('FAIL:', m, '->', e)
        traceback.print_exc()
