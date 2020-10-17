import numpy as np
import tensorflow as tf
from keras import metrics, losses, optimizers
from keras.models import Model, Sequential
from keras.layers import (
    Dense,
    Input,
    Dropout,
    Flatten
)
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.utils import np_utils

from scipy import signal
import matplotlib.pyplot as plt


def readfile(filename, label):
    data = np.loadtxt(filename, delimiter="\t")
    x = data
    y = label * np.ones(data.shape[0])
    return x, y.astype(int)


def spec_data(x, fs, plot=False):
    f, t, Sxx = signal.spectrogram(x, fs, nfft=x.shape[0])
    Sxx = np.abs(Sxx)
    if plot:
        plt.pcolormesh(t, f, Sxx, shading="gouraud")
        plt.ylabel("Frequency [Hz]")
        plt.xlabel("Time [sec]")
        plt.show()
    return Sxx


def get_data():
    mode2_x, mode2_y = readfile("mode2.csv", 0)
    mode3_x, mode3_y = readfile("mode3.csv", 1)
    mode4_x, mode4_y = readfile("mode4.csv", 2)

    # Merge two sample sets
    x = np.concatenate((mode2_x, mode3_x, mode4_x), axis=0)
    y = np.concatenate((mode2_y, mode3_y, mode4_y), axis=0)

    # Inspect
    # fs = 256000
    # frame = 30
    # x_seg = mode2_x[frame,:]
    # spec_data(x_seg, fs, True)
    # x_seg = mode3_x[frame,:]
    # spec_data(x_seg, fs, True)
    # x_seg = mode3_x[frame,:]
    # spec_data(x_seg, fs, True)

    # Transform
    fs = 256000
    for i in range(x.shape[0]):
        x_seg = x[i, :]
        sxx = spec_data(x_seg, fs) / x_seg.shape[0]
        sxx = sxx.reshape((1, sxx.shape[0], sxx.shape[1]))
        if i == 0:
            x_sxx = sxx
        else:
            x_sxx = np.vstack((x_sxx, sxx))

    x = x_sxx
    print("max", np.max(x))
    print("min", np.min(x))
    print("shape", x.shape)

    # Split into train and test
    train_percent = 0.5
    columns = x.shape[0]
    train_columns = int(np.floor(train_percent * columns))
    print(train_columns)

    # Shuffle
    idx = np.random.permutation(len(y))
    x = x[idx]
    y = y[idx]

    x_train = x[:train_columns, :]
    y_train = y[:train_columns]
    x_test = x[train_columns:, :]
    y_test = y[train_columns:]

    num_classes = len(np.unique(y))
    y_train = np_utils.to_categorical(y_train, num_classes)
    y_test = np_utils.to_categorical(y_test, num_classes)

    # Add a fourth column for input spec
    x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], x_train.shape[2], 1))
    x_test = x_test.reshape((x_test.shape[0], x_test.shape[1], x_test.shape[2], 1))

    print("num_classes", num_classes)
    return x_train, y_train, x_test, y_test, num_classes


def create_model_nn(x_train, y_train, x_test, y_test, n_outputs):

    input_shape = (x_train.shape[1], x_train.shape[2], x_train.shape[3])

    model = Sequential()
    model.add(Dense(32, activation="relu", input_shape=input_shape))
    model.add(Flatten())
    model.add(Dense(128, activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation="softmax"))
    # Compile
    model.compile(
        loss=losses.categorical_crossentropy,
        optimizer=optimizers.adam(),
        metrics=["accuracy"],
    )
    print(model.summary())
    # Train and test
    model.fit(
        x_train,
        y_train,
        batch_size=4,
        epochs=100,
        verbose=1,
        validation_data=(x_test, y_test),
    )


def create_model_cnn(x_train, y_train, x_test, y_test, n_outputs):

    input_shape = (x_train.shape[1], x_train.shape[2], x_train.shape[3])

    model = Sequential()
    model.add(Conv2D(4, kernel_size=(3, 3), activation="relu", input_shape=input_shape))
    model.add(Conv2D(8, kernel_size=(3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(32, activation="relu"))
    model.add(Dropout(0.1))
    model.add(Dense(num_classes, activation="softmax"))
    # Compile
    model.compile(
        loss=losses.categorical_crossentropy,
        optimizer=optimizers.adam(),
        metrics=["accuracy"],
    )
    print(model.summary())
    # Train and test
    model.fit(
        x_train,
        y_train,
        batch_size=8,
        epochs=100,
        verbose=1,
        validation_data=(x_test, y_test),
    )

# Import data and run model
x_train, y_train, x_test, y_test, num_classes = get_data()
create_model_cnn(x_train, y_train, x_test, y_test, num_classes)
