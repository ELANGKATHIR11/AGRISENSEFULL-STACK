try:
    import numpy as np
except Exception:
    np = None

import types as _types
# Prefer lightweight tflite_runtime; fall back to TensorFlow Lite if available
try:
    import tflite_runtime.interpreter as tflite  # type: ignore
except Exception:
    try:
        from tensorflow.lite import Interpreter as _TfInterpreter  # type: ignore
        tflite = _types.SimpleNamespace(Interpreter=_TfInterpreter)
    except Exception:
        tflite = None  # Will trigger fallback rules below

try:
    if tflite is not None:
        interpreter = tflite.Interpreter(model_path='models/irrigation_model.tflite')
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
    else:
        interpreter = None
        input_details = None
        output_details = None
except Exception:
    interpreter = None
    input_details = None
    output_details = None
    print('⚠️ ML model not found, using fallback rules.')

def predict_irrigation(features):
    if interpreter and np is not None and input_details is not None and output_details is not None:
        input_data = np.array([features], dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        return float(output[0][0])
    else:
        soil_moisture = features[0]
        return 500 if soil_moisture < 35 else 0
