import onnxruntime


class OnnxInfer:
    def __init__(self, onnx_model_path, input_name="obs", awd=False):
        self.onnx_model_path = onnx_model_path
        self.ort_session = onnxruntime.InferenceSession(
            self.onnx_model_path, providers=["CPUExecutionProvider"]
        )
        self.input_name = input_name
        self.awd = awd

    def infer(self, inputs):
        if self.awd:
            outputs = self.ort_session.run(None, {self.input_name: [inputs]})
            return outputs[0][0]
        else:
            outputs = self.ort_session.run(
                None, {self.input_name: inputs.astype("float32")}
            )
            return outputs[0]


if __name__ == "__main__":
    import argparse
    import numpy as np
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--onnx_model_path", type=str, required=True)
    args = parser.parse_args()

    oi = OnnxInfer(args.onnx_model_path, awd=True)
    inputs = np.random.uniform(size=54).astype(np.float32)
    inputs = np.arange(47).astype(np.float32)
    times = []
    for i in range(1000):
        start = time.time()
        print(oi.infer(inputs))
        times.append(time.time() - start)

    print("Average time: ", sum(times) / len(times))
    print("Average fps: ", 1 / (sum(times) / len(times)))
