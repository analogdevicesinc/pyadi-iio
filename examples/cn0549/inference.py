import numpy as np
from scipy import signal
from tflite_runtime.interpreter import Interpreter


# Utils
def spec_data(x, fs, plot=False, title=""):
    f, t, Sxx = signal.spectrogram(x, fs, nfft=x.shape[0])
    return np.abs(Sxx)


def readfile(filename, label):
    data = np.loadtxt(filename, delimiter="\t")
    x = data
    y = label * np.ones(data.shape[0])
    return x, y.astype(int)


def set_input_tensor(interpreter, sxx):
    tensor_index = interpreter.get_input_details()[0]["index"]
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = sxx


###################################

simulate = True
fs = 256000

if not simulate:
    import adi

    # initialization
    xl = adi.cn0532()
    xl.rx_buffer_size = 2 ** 12
    xl.sample_rate = fs

    loops = 1024
else:
    mode2_x, mode2_y = readfile("mode2.csv", 1)
    mode3_x, mode3_y = readfile("mode3.csv", 1)
    mode4_x, mode4_y = readfile("mode4.csv", 1)
    s = mode3_x.shape
    x = mode4_x
    loops = x.shape[0]


interpreter = Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()
labels = ["Sleep", "General", "Allergen"]


for it in range(loops):

    # print(mode3_x[k,:])

    # Collect data
    if simulate:
        x_seg = x[it, :]
    else:
        x_seg = xl.rx()

    # Transform
    sxx = spec_data(x_seg, fs) / x_seg.shape[0]
    sxx = sxx.reshape((sxx.shape[0], sxx.shape[1], 1))

    # Classify
    set_input_tensor(interpreter, sxx)
    interpreter.invoke()
    output_details = interpreter.get_output_details()[0]
    output = np.squeeze(interpreter.get_tensor(output_details["index"]))

    # View
    out = ""
    for l, o in zip(labels, output):
        out += f"{l}: {o} | "
    out = out[:-2]
    w = np.argmax(output)

    it += 1
    print(f"Iteration {it}")
    print(f"  Probabilities: {out}\n  Winner: {labels[w]}")
