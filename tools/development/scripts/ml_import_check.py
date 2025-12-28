import importlib
modules = ['codecarbon','sentence_transformers','torch','faiss']
for m in modules:
    try:
        mo = importlib.import_module(m)
        v = getattr(mo, '__version__', None) or getattr(mo, 'VERSION', None) or 'unknown'
        print(m, 'OK', v)
    except Exception as e:
        print(m, 'FAILED ->', type(e).__name__, e)
