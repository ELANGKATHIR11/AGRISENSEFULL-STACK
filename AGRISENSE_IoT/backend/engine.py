import numpy as np
import tflite_runtime.interpreter as tflite

try:
    interpreter = tflite.Interpreter(model_path='models/irrigation_model.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
except:
    interpreter = None
    print('⚠️ ML model not found, using fallback rules.')

def predict_irrigation(features):
    if interpreter:
        input_data = np.array([features], dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        return float(output[0][0])
    else:
        soil_moisture = features[0]
        return 500 if soil_moisture < 35 else 0
