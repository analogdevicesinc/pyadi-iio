import test.rf.spec as spec
import time

import adi
import numpy as np
import pytest


def dma_rx(uri, classname, channel):
    """ dma_rx: Construct RX buffers and verify data is non-zero when pulled.
        Collected buffer is of size 2**15 and 10 buffers are checked

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through rx_enabled_channels
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    N = 2 ** 15
    sdr.rx_enabled_channels = channel if isinstance(channel, list) else [channel]
    sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)
    try:
        for _ in range(10):
            data = sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert np.sum(np.abs(data)) > 0
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def dma_tx(uri, classname, channel):
    """ dma_tx: Construct TX buffers and verify no errors occur when pushed.
        Buffer is of size 2**15 and 10 buffers are pushed

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    TXFS = 1000
    N = 2 ** 15
    ts = 1 / float(TXFS)
    t = np.arange(0, N * ts, ts)
    fc = 10000
    d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5

    if not isinstance(channel, list):
        sdr.tx_enabled_channels = [channel]
    else:
        sdr.tx_enabled_channels = channel
        d = [d] * len(channel)
    sdr.tx_buffer_size = N * len(sdr.tx_enabled_channels)

    try:
        for _ in range(10):
            sdr.tx(d)
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def dma_loopback(uri, classname, channel):
    """ dma_loopback: Test DMA digital loopback with a triangle waveforms.
        This test requires a AD936x or similar device with internal loopback
        modes. A triangle wave is generated on I and Q or real1 and real2
        and multiple periods are compared for missing samples within a buffer
        and delay between buffers.

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    if classname == "adi.FMComms5" and (channel in [2, 3]):
        sdr.loopback_chip_b = 1
    else:
        sdr.loopback = 1
    sdr.tx_cyclic_buffer = True
    # Create a ramp signal with different values for I and Q
    start = 0
    tx_data = np.array(range(start, 2 ** 11), dtype=np.int16)
    tx_data = tx_data << 4
    tx_data = tx_data + 1j * (tx_data * -1 - 1)
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = len(tx_data) * 2 * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = len(tx_data) * 2 * len(sdr.rx_enabled_channels)
    try:
        sdr.tx(tx_data)
        # Flush buffers
        for _ in range(100):
            data = sdr.rx()
        # Turn off loopback (for other tests)
        if classname == "adi.FMComms5" and (channel in [2, 3]):
            sdr.loopback_chip_b = 0
        else:
            sdr.loopback = 0
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    # Check data
    offset = 0
    for i in range(len(data)):
        if np.real(data[i]) == start:
            for d in range(len(tx_data)):
                # print(str(data[i+offset])+" "+str(d+start))
                assert np.real(data[i + offset]) == (d + start)
                assert np.imag(data[i + offset]) == ((d + start) * -1 - 1)
                offset = offset + 1
            break


def freq_est(y, fs):
    N = len(y)
    T = 1.0 / fs
    yf = np.fft.fft(y)
    yf = np.fft.fftshift(yf)
    xf = np.linspace(-1.0 / (2.0 * T), 1.0 / (2.0 * T), N)
    # if self.do_plots:
    #     import matplotlib.pyplot as plt
    #
    #     fig, ax = plt.subplots()
    #     ax.plot(xf, 2.0 / N * np.abs(yf))
    #     plt.show()
    indx = np.argmax(np.abs(yf))
    return xf[indx]


def dds_loopback(uri, classname, param_set, channel, frequency, scale, peak_min):
    """ dds_loopback: Test DDS loopback with connected loopback cables.
        This test requires a devices with TX and RX onboard where the transmit
        signal can be recovered. TX FPGA DDSs are used to generate a sinusoid
        which is then estimated on the RX side. The receive tone must be within
        1% of its expected frequency with a specified peak

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            param_set: type=dict
                Dictionary of attribute and values to be set before tone is
                generated and received
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            frequency: type=integer
                Frequency in Hz of transmitted tone
            scale: type=float
                Scale of DDS tone. Range [0,1]
            peak_min: type=float
                Minimum acceptable value of maximum peak in dBFS of received tone

    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    # Set common buffer settings
    sdr.tx_cyclic_buffer = True
    N = 2 ** 14
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.rx_sample_rate)

    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    sdr.dds_single_tone(frequency, scale, channel)

    # Pass through SDR
    try:
        for _ in range(10):  # Wait
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=2 ** 15)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - frequency)
    print("Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx]))
    assert (frequency * 0.01) > diff
    assert tone_peaks[indx] > peak_min


def cw_loopback(uri, classname, channel, param_set):
    """ cw_loopback: Test CW loopback with connected loopback cables.
        This test requires a devices with TX and RX onboard where the transmit
        signal can be recovered. Sinuoidal data is passed to DMAs which is then
        estimated on the RX side. The receive tone must be within
        1% of its expected frequency at the max peak found

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            param_set: type=dict
                Dictionary of attribute and values to be set before tone is
                generated and received
    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    time.sleep(1)
    # Verify still set
    for p in param_set.keys():
        if isinstance(param_set[p], str):
            assert getattr(sdr, p) == param_set[p]
        else:
            assert np.abs(getattr(sdr, p) - param_set[p]) < 4
    # Set common buffer settings
    sdr.tx_cyclic_buffer = True
    N = 2 ** 14
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    elif hasattr(sdr, "rx_sample_rate"):
        RXFS = int(sdr.rx_sample_rate)
    else:
        """ no sample_rate nor rx_sample_rate. Let's try something like
        rx($channel)_sample_rate"""
        attr = "rx" + str(channel) + "_sample_rate"
        RXFS = int(getattr(sdr, attr))

    A = 2 ** 15
    fc = RXFS * 0.1
    ts = 1 / float(RXFS)
    t = np.arange(0, N * ts, ts)
    if sdr._complex_data:
        i = np.cos(2 * np.pi * t * fc) * A * 0.5
        q = np.sin(2 * np.pi * t * fc) * A * 0.5
        cw = i + 1j * q
    else:
        cw = np.cos(2 * np.pi * t * fc) * A * 1

    # Pass through SDR
    try:
        sdr.tx(cw)
        for _ in range(30):  # Wait to stabilize
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    # tone_freq = freq_est(data, RXFS)
    # diff = np.abs(tone_freq - fc)
    # print("Peak: @"+str(tone_freq) )
    # assert (fc * 0.01) > diff

    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=A)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - fc)
    print("Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx]))
    assert (fc * 0.01) > diff
    # self.assertGreater(fc * 0.01, diff, "Frequency offset")


def t_sfdr(uri, classname, channel, param_set, sfdr_min):
    """ t_sfdr: Test SFDR loopback of tone with connected loopback cables.
        This test requires a devices with TX and RX onboard where the transmit
        signal can be recovered. Sinuoidal data is passed to DMAs which is then
        estimated on the RX side. The peak and second peak are determined in
        the received signal to determine the sfdr.

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            param_set: type=dict
                Dictionary of attribute and values to be set before tone is
                generated and received
            sfdr_min: type=float
                Minimum acceptable value of SFDR in dB

    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    time.sleep(5)  # Wait for QEC to kick in
    # Set common buffer settings
    N = 2 ** 14
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.rx_sample_rate)
    fc = RXFS * 0.1

    ts = 1 / float(RXFS)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.9
    q = np.sin(2 * np.pi * t * fc) * 2 ** 15 * 0.9
    iq = i + 1j * q
    # Pass through SDR
    try:
        sdr.tx(iq)
        time.sleep(3)
        for _ in range(10):  # Wait for IQ correction to stabilize
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    val = spec.sfdr(data, plot=False)
    assert val > sfdr_min


def gain_check(uri, classname, channel, param_set, dds_scale, min_rssi, max_rssi):
    """ gain_check: Test DDS loopback with connected loopback cables and verify
        calculated RSSI. This is only applicable for devices with RSSI calculations
        onboard. This test also requires a devices with TX and RX onboard where the
        transmit signal can be recovered. TX FPGA DDSs are used to generate a
        sinusoid which is then received on the RX side. RSSI is captured during
        this reception. The generated tone is at 10% RX sample rate.

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            param_set: type=dict
                Dictionary of attribute and values to be set before tone is
                generated and received
            dds_scale: type=float
                Scale of DDS tone. Range [0,1]
            min_rssi: type=float
                Minimum acceptable value of RSSI attribute
            max_rssi: type=float
                Maximum acceptable value of RSSI attribute

    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    # Enable DDSs
    if hasattr(sdr, "sample_rate"):
        fs = int(sdr.sample_rate)
    else:
        fs = int(sdr.rx_sample_rate)
    sdr.dds_single_tone(np.floor(fs * 0.1), dds_scale, channel)
    time.sleep(3)

    # Check RSSI
    if channel == 0:
        rssi = sdr._get_iio_attr("voltage0", "rssi", False, sdr._ctrl)
    if channel == 1:
        rssi = sdr._get_iio_attr("voltage1", "rssi", False, sdr._ctrl)
    if channel == 2:
        rssi = sdr._get_iio_attr("voltage0", "rssi", False, sdr._ctrl_b)
    if channel == 3:
        rssi = sdr._get_iio_attr("voltage1", "rssi", False, sdr._ctrl_b)
    if channel == 4:
        rssi = sdr._get_iio_attr("voltage0", "rssi", False, sdr._ctrl_c)
    if channel == 5:
        rssi = sdr._get_iio_attr("voltage1", "rssi", False, sdr._ctrl_c)
    if channel == 6:
        rssi = sdr._get_iio_attr("voltage0", "rssi", False, sdr._ctrl_d)
    if channel == 7:
        rssi = sdr._get_iio_attr("voltage1", "rssi", False, sdr._ctrl_d)

    print(rssi)
    assert rssi >= min_rssi
    assert rssi <= max_rssi


def cyclic_buffer(uri, classname, channel, param_set):
    """ cyclic_buffer: Construct Cyclic TX buffers and verify
        no errors occur when pushed. This is performed twice
        without closing the context

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            param_set: type=dict
                Dictionary of attribute and values to be set before tone is
                generated
    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    fs = int(sdr.sample_rate)
    fc = -3000000
    N = 1024
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = i + 1j * q
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    sdr.tx(iq)
    sdr.tx_destroy_buffer()
    fail = False
    try:
        sdr.tx(iq)
    except Exception as e:
        fail = True
        msg = (
            "Pushing new data after destroying buffer should not fail. "
            "message: " + str(e)
        )

    # Cleanly end
    del sdr
    if fail:
        pytest.fail(msg)


def cyclic_buffer_exception(uri, classname, channel, param_set):
    """ cyclic_buffer_exception: Construct Cyclic TX buffers and verify
        errors occur when pushed. This is performed twice
        without closing the context and with resetting the TX buffers
        which should cause an exception

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            param_set: type=dict
                Dictionary of attribute and values to be set before tone is
                generated
    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])
    fs = int(sdr.sample_rate)
    fc = -3000000
    N = 1024
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 14
    q = np.sin(2 * np.pi * t * fc) * 2 ** 14
    iq = i + 1j * q
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)
    try:
        sdr.tx(iq)
        sdr.tx(iq)
    except Exception as e:
        if (
            "TX buffer has been submitted in cyclic mode. "
            "To push more data the tx buffer must be destroyed first." not in str(e)
        ):
            fail = True
            msg = "Wrong exception raised, message was: " + str(e)
        else:
            fail = False
    else:
        fail = True
        msg = "ExpectedException not raised"
    # Cleanly end
    del sdr
    if fail:
        pytest.fail(msg)


#########################################


def stress_context_creation(uri, classname, channel, repeats):
    """ stress_context_creation: Repeatedly create and destroy a context

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            repeats: type=integer
                Number of times to re-create contexts
    """
    for _ in range(repeats):
        # bi = BoardInterface(classname, devicename)
        sdr = eval(classname + "(uri='" + uri + "')")
        N = 2 ** 15
        sdr.rx_enabled_channels = channel if isinstance(channel, list) else [channel]
        sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)
        try:
            for _ in range(repeats):
                data = sdr.rx()
                if isinstance(data, list):
                    for chan in data:
                        assert np.sum(np.abs(chan)) > 0
                else:
                    assert np.sum(np.abs(data)) > 0
                sdr.rx_destroy_buffer()
        except Exception as e:
            del sdr
            raise Exception(e)

        del sdr


def stress_rx_buffer_length(uri, classname, channel, buffer_sizes):
    """ stress_rx_buffer_length: Repeatedly create and destroy buffers across different buffer sizes

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            buffer_sizes: type=list
                List of buffer size to create and collect
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    sdr.rx_enabled_channels = channel if isinstance(channel, list) else [channel]
    try:
        for size in buffer_sizes:
            sdr.rx_buffer_size = size
            data = sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert len(chan) == size
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert len(data) == size
                assert np.sum(np.abs(data)) > 0
            sdr.rx_destroy_buffer()
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def stress_rx_buffer_creation(uri, classname, channel, repeats):
    """ stress_rx_buffer_creation: Repeatedly create and destroy buffers

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            repeats: type=integer
                Number of times to re-create contexts
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    N = 2 ** 15
    sdr.rx_enabled_channels = channel if isinstance(channel, list) else [channel]
    sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)
    try:
        for _ in range(repeats):
            data = sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert np.sum(np.abs(data)) > 0
            sdr.rx_destroy_buffer()
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def stress_tx_buffer_creation(uri, classname, channel, repeats):
    """ stress_tx_buffer_creation: Repeatedly create and destroy TX buffers

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            repeats: type=integer
                Number of times to re-create buffers
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    TXFS = 1000
    N = 2 ** 15
    ts = 1 / float(TXFS)
    t = np.arange(0, N * ts, ts)
    fc = 10000
    d = np.cos(2 * np.pi * t * fc) * 2 ** 15 * 0.5

    if not isinstance(channel, list):
        sdr.tx_enabled_channels = [channel]
    else:
        sdr.tx_enabled_channels = channel
        d = [d] * len(channel)
    sdr.tx_buffer_size = N * len(sdr.tx_enabled_channels)

    try:
        for _ in range(repeats):
            sdr.tx(d)
            sdr.tx_destroy_buffer()
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr
