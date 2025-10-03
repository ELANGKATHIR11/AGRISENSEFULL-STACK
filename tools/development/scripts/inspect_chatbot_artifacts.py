"""
Small helper: inspect chatbot artifacts (npz + json) in both candidate backend paths and print info.
"""
import json
import os
import sys
import numpy as np

CANDIDATES = [
    r"D:\AGRISENSE FULL-STACK\agrisense_app\backend",
    r"D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\backend",
]


def inspect_dir(d):
    print('Inspecting:', d)
    npz = os.path.join(d, 'chatbot_index.npz')
    js1 = os.path.join(d, 'chatbot_index.json')
    js2 = os.path.join(d, 'chatbot_qa_pairs.json')
    for p in (npz, js1, js2):
        print('  exists:', os.path.exists(p), '->', p)
    if os.path.exists(npz):
        try:
            data = np.load(npz, allow_pickle=True)
            print('  NPZ keys:', list(data.keys()))
            if 'embeddings' in data:
                arr = data['embeddings']
                print('  embeddings shape:', getattr(arr, 'shape', 'unknown'), 'dtype:', getattr(arr, 'dtype', None))
            else:
                print("  WARNING: 'embeddings' key not found in npz")
        except Exception as e:
            print('  Failed to read npz:', e)
    for j in (js1, js2):
        if os.path.exists(j):
            try:
                with open(j, 'r', encoding='utf-8') as fh:
                    obj = json.load(fh)
                print('  JSON', os.path.basename(j), 'keys/top-level:', (list(obj.keys()) if isinstance(obj, dict) else type(obj)))
            except Exception as e:
                print('  Failed to read json', j, e)


if __name__ == '__main__':
    for d in CANDIDATES:
        inspect_dir(d)
    sys.exit(0)
