import heapq
import test.rf.spec as spec
#import genalyzer
import time

import adi
import numpy as np
import pytest
from numpy.fft import fft, fftfreq, fftshift
from scipy import signal

try:
    from .plot_logger import gen_line_plot_html

    do_html_log = True
except:
    do_html_log = False


def dma_rx(uri, classname, channel, use_rx2=False):
    """dma_rx: Construct RX buffers and verify data is non-zero when pulled.
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

    if use_rx2:
        sdr.rx2_enabled_channels = channel if isinstance(channel, list) else [channel]
        sdr.rx2_buffer_size = N * len(sdr.rx2_enabled_channels)
    else:
        sdr.rx_enabled_channels = channel if isinstance(channel, list) else [channel]
        sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)

    try:
        for _ in range(10):
            data = sdr.rx2() if use_rx2 else sdr.rx()
            if isinstance(data, list):
                for chan in data:
                    assert np.sum(np.abs(chan)) > 0
            else:
                assert np.sum(np.abs(data)) > 0
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def dma_tx(uri, classname, channel, use_tx2=False):
    """dma_tx: Construct TX buffers and verify no errors occur when pushed.
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

    if use_tx2:
        if not isinstance(channel, list):
            sdr.tx2_enabled_channels = [channel]
        else:
            sdr.tx2_enabled_channels = channel
            d = [d] * len(channel)
        sdr.tx2_buffer_size = N * len(sdr.tx2_enabled_channels)
    else:
        if not isinstance(channel, list):
            sdr.tx_enabled_channels = [channel]
        else:
            sdr.tx_enabled_channels = channel
            d = [d] * len(channel)
        sdr.tx_buffer_size = N * len(sdr.tx_enabled_channels)

    try:
        for _ in range(10):
            sdr.tx2(d) if use_tx2 else sdr.tx(d)
    except Exception as e:
        del sdr
        raise Exception(e)

    del sdr


def dma_dac_zeros(uri, classname, channel):
    """dma_dac_zeros: Test DMA digital loopback with a zeros.
    This test requires a AD936x or similar device with internal loopback
    modes. The TX cores are put into zero source mode in cases when no
    output is desired

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
    sdr.tx_enabled_channels = None
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = 2 ** 11 * 2 * len(sdr.rx_enabled_channels)
    try:
        sdr.tx()
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
    assert sum(np.abs(data)) == 0


def dma_loopback(uri, classname, channel):
    """dma_loopback: Test DMA digital loopback with a triangle waveforms.
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


def dds_loopback(
    uri,
    classname,
    param_set,
    channel,
    frequency,
    scale,
    peak_min,
    use_obs=False,
    use_rx2=False,
):
    """dds_loopback: Test DDS loopback with connected loopback cables.
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

    if use_obs and use_rx2:
        raise Exception("Both RX2 and OBS are selected. Select one at a time.")

    if use_rx2:
        sdr.rx2_enabled_channels = [channel]
        sdr.rx2_buffer_size = N * 2 * len(sdr.rx2_enabled_channels)
    elif use_obs:
        sdr.obs.rx_enabled_channels = [0]
        sdr.obs.rx_buffer_size = N * 2 * len(sdr.obs.rx_enabled_channels)
    else:
        sdr.rx_enabled_channels = [channel]
        sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)

    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.orx_sample_rate) if use_obs else int(sdr.rx_sample_rate)

    sdr.dds_single_tone(frequency, scale, channel)

    # Pass through SDR
    try:
        for _ in range(10):  # Wait
            data = sdr.rx2() if use_rx2 else sdr.obs.rx() if use_obs else sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=2 ** 15, plot=False)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - frequency)
    s = "Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx])
    print(s)

    if do_html_log:
        pytest.data_log = {
            "html": gen_line_plot_html(
                tone_freqs,
                tone_peaks,
                "Frequency (Hz)",
                "Amplitude (dBFS)",
                "{} ({})".format(s, classname),
            )
        }

    assert (frequency * 0.01) > diff
    assert tone_peaks[indx] > peak_min


def dds_two_tone(
    uri,
    classname,
    channel,
    param_set,
    frequency1,
    scale1,
    peak_min1,
    frequency2,
    scale2,
    peak_min2,
):
    """
    dds_two_tone: Test DDS loopback with connected loopback cables.
    This test requires a devices with TX and RX onboard where the transmit
    signal can be recovered. TX FPGA DDSs are used to generate two sinusoids
    which are then estimated on the RX side. The receive tones must be within
    1% of its respective expected frequency with a specified peak.

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
        frequency1: type=integer
            Frequency in Hz of the first transmitted tone
        scale1: type=float
            Scale of the first DDS tone. Range [0,1]
        peak_min1: type=float
            Minimum acceptable value of maximum peak in dBFS of the received
            first tone
        frequency2: type=integer
            Frequency in Hz of the second transmitted tone
        scale2: type=float
            Scale of the second DDS tone. Range [0,1]
        peak_min2: type=float
            Minimum acceptable value of maximum peak in dBFS of the received
            second tone

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
    sdr.dds_dual_tone(frequency1, scale1, frequency2, scale2, channel)

    # Pass through SDR
    try:
        for _ in range(10):  # Wait
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=2 ** 15)
    indx = heapq.nlargest(2, range(len(tone_peaks)), tone_peaks.__getitem__)
    s1 = "Peak 1: " + str(tone_peaks[indx[0]]) + " @ " + str(tone_freqs[indx[0]])
    s2 = "Peak 2: " + str(tone_peaks[indx[1]]) + " @ " + str(tone_freqs[indx[1]])
    print(s1)
    print(s2)

    if do_html_log:
        pytest.data_log = {
            "html": gen_line_plot_html(
                tone_freqs,
                tone_peaks,
                "Frequency (Hz)",
                "Amplitude (dBFS)",
                "{}\n{} ({})".format(s1, s2, classname),
            )
        }

    if (abs(frequency1 - tone_freqs[indx[0]]) <= (frequency1 * 0.01)) and (
        abs(frequency2 - tone_freqs[indx[1]]) <= (frequency2 * 0.01)
    ):
        diff1 = np.abs(tone_freqs[indx[0]] - frequency1)
        diff2 = np.abs(tone_freqs[indx[1]] - frequency2)
        # print(frequency1, frequency2)
        # print(tone_freqs[indx[0]], tone_freqs[indx[1]])
        # print(tone_peaks[indx[0]], tone_peaks[indx[1]])
        # print(diff1, diff2)
        assert (frequency1 * 0.01) > diff1
        assert (frequency2 * 0.01) > diff2
        assert tone_peaks[indx[0]] > peak_min1
        assert tone_peaks[indx[1]] > peak_min2
    elif (abs(frequency2 - tone_freqs[indx[0]]) <= (frequency2 * 0.01)) and (
        abs(frequency1 - tone_freqs[indx[1]]) <= (frequency1 * 0.01)
    ):
        diff1 = np.abs(tone_freqs[indx[0]] - frequency2)
        diff2 = np.abs(tone_freqs[indx[1]] - frequency1)
        assert (frequency2 * 0.01) > diff1
        assert (frequency1 * 0.01) > diff2
        assert tone_peaks[indx[1]] > peak_min1
        assert tone_peaks[indx[0]] > peak_min2


def nco_loopback(uri, classname, param_set, channel, frequency, peak_min):
    """nco_loopback: TX/DAC Test tone loopback with connected loopback cables.
    This test requires a devices with TX and RX onboard where the transmit
    signal can be recovered. TX/DAC internal NCOs are used to generate a sinusoid
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
        peak_min: type=float
            Minimum acceptable value of maximum peak in dBFS of received tone

    """
    # See if we can tone using DMAs
    sdr = eval(classname + "(uri='" + uri + "')")
    # Set custom device parameters
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])

    N = 2 ** 14
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)
    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    elif hasattr(sdr, "rx_sample_rate"):
        RXFS = int(sdr.rx_sample_rate)
    else:
        """no sample_rate nor rx_sample_rate. Let's try something like
        rx($channel)_sample_rate"""
        attr = "rx" + str(channel) + "_sample_rate"
        RXFS = int(getattr(sdr, attr))

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
    s = "Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx])
    print(s)
    if do_html_log:
        pytest.data_log = {
            "html": gen_line_plot_html(
                tone_freqs,
                tone_peaks,
                "Frequency (Hz)",
                "Amplitude (dBFS)",
                "{} ({})".format(s, classname),
            )
        }

    assert (frequency * 0.01) > diff
    assert tone_peaks[indx] > peak_min


def cw_loopback(uri, classname, channel, param_set, use_tx2=False, use_rx2=False):
    """cw_loopback: Test CW loopback with connected loopback cables.
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
        use_tx2: type=bool
            Boolean if set will use tx2() as tx method
        use_rx2: type=bool
            Boolean if set will use rx2() as rx method
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
            assert (
                np.argmax(np.abs(np.array(getattr(sdr, p)) - np.array(param_set[p])))
                < 4
            )
    # Set common buffer settings
    N = 2 ** 14
    if use_tx2:
        sdr.tx2_cyclic_buffer = True
        sdr.tx2_enabled_channels = [channel]
        sdr.tx2_buffer_size = N * 2 * len(sdr.tx2_enabled_channels)
    else:
        sdr.tx_cyclic_buffer = True
        sdr.tx_enabled_channels = [channel]
        sdr.tx_buffer_size = N * 2 * len(sdr.tx_enabled_channels)

    if use_rx2:
        sdr.rx2_enabled_channels = [channel]
        sdr.rx2_buffer_size = N * 2 * len(sdr.rx2_enabled_channels)
    else:
        sdr.rx_enabled_channels = [channel]
        sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)

    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    elif hasattr(sdr, "rx_sample_rate"):
        RXFS = int(sdr.rx_sample_rate)
    else:
        """no sample_rate nor rx_sample_rate. Let's try something like
        rx($channel)_sample_rate"""
        attr = "rx" + str(channel) + "_sample_rate"
        RXFS = int(getattr(sdr, attr))

    A = 2 ** 15
    fc = RXFS * 0.1
    fc = int(fc / (RXFS / N)) * (RXFS / N)

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
        if use_tx2:
            sdr.tx2(cw)
        else:
            sdr.tx(cw)
        for _ in range(60):  # Wait to stabilize
            data = sdr.rx2() if use_rx2 else sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    # tone_freq = freq_est(data, RXFS)
    # diff = np.abs(tone_freq - fc)
    # print("Peak: @"+str(tone_freq) )
    # assert (fc * 0.01) > diff

    tone_peaks, tone_freqs = spec.spec_est(data, fs=RXFS, ref=A, plot=False)
    indx = np.argmax(tone_peaks)
    diff = np.abs(tone_freqs[indx] - fc)
    s = "Peak: " + str(tone_peaks[indx]) + "@" + str(tone_freqs[indx])
    print(s)
    print("Freqs:")
    print(tone_freqs)
    print("Amps: ")
    print(tone_peaks)
    if do_html_log:
        pytest.data_log = {
            "html": gen_line_plot_html(
                tone_freqs,
                tone_peaks,
                "Frequency (Hz)",
                "Amplitude (dBFS)",
                "{} ({})".format(s, classname),
            )
        }

    assert (fc * 0.01) > diff
    # self.assertGreater(fc * 0.01, diff, "Frequency offset")


def t_sfdr(uri, classname, channel, param_set, sfdr_min, use_obs=False, full_scale=0.9):
    """t_sfdr: Test SFDR loopback of tone with connected loopback cables.
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

    if use_obs:
        sdr.obs.rx_enabled_channels = [0]
        sdr.obs.rx_buffer_size = N * 2 * len(sdr.obs.rx_enabled_channels)
    else:
        sdr.rx_enabled_channels = [channel]
        sdr.rx_buffer_size = N * 2 * len(sdr.rx_enabled_channels)

    # Create a sinewave waveform
    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.rx_sample_rate)

    fc = RXFS * 0.1
    fc = int(fc / (RXFS / N)) * (RXFS / N)

    ts = 1 / float(RXFS)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 15 * full_scale
    q = np.sin(2 * np.pi * t * fc) * 2 ** 15 * full_scale
    iq = i + 1j * q
    # Pass through SDR
    try:
        sdr.tx(iq)
        time.sleep(3)
        for _ in range(10):  # Wait for IQ correction to stabilize
            data = sdr.obs.rx() if use_obs else sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    valr, amp, freqs = spec.sfdr(data, plot=False)
    # CALL GENALYZER
    config_dict = {
        "domain_wf": 0,
        "fs": RXFS,
        "fsr": 2,
        "navg": 1,
        "nfft": len(data),
        "res": 16,
        "type_wf": 2,
    }
    c = genalyzer.config_tone_meas(config_dict)
    d = []
    for dd in data:
        d += [int(np.real(dd))]
        d += [int(np.imag(dd))]
    val = genalyzer.metric_t(c, d, "SFDR")

    if do_html_log:
        pytest.data_log = {
            "html": gen_line_plot_html(
                freqs,
                amp,
                "Frequency (Hz)",
                "Amplitude (dBFS)",
                "SDFR {} dBc ({})".format(val, classname),
            )
        }
    print("SFDR:", val, "dB",f"(old {valr})")
    assert val > sfdr_min


def gain_check(uri, classname, channel, param_set, dds_scale, min_rssi, max_rssi):
    """gain_check: Test DDS loopback with connected loopback cables and verify
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
    time.sleep(5)

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


def hardwaregain(
    uri,
    classname,
    channel,
    dds_scale,
    frequency,
    hardwaregain_low,
    hardwaregain_high,
    param_set,
):
    """ hadwaregain: Test loopback with connected cables and verify
        calculated hardware gain, by measuring changes in the AGC. This is only applicable
        for devices with RSSI calculations onboard. This test also requires a devices
        with TX and RX onboard where the transmit signal can be recovered. TX FPGA
        DDSs are used to generate a sinusoid which is then received on the RX side.

        parameters:
            uri: type=string
                URI of IIO context of target board/system
            classname: type=string
                Name of pyadi interface class which contain attribute
            channel: type=list
                List of integers or list of list of integers of channels to
                enable through tx_enabled_channels
            dds_scale: type=float
                Scale of DDS tone. Range [0,1]
            frequency:
                Frequency in hertz of the generated tone. This must be
                less than 1/2 the sample rate.
            hardwaregain_low: type=float
                Minimum acceptable value of hardwaregain attribute
            hardwaregain_high: type=float
                Maximum acceptable value of hardwaregain attribute

    """
    sdr = eval(classname + "(uri='" + uri + "')")

    # set custom attrs
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])

    sdr.dds_single_tone(frequency, dds_scale, channel)

    time.sleep(5)

    if channel == 0:
        hwgain = sdr._get_iio_attr("voltage0", "hardwaregain", False, sdr._ctrl)
    if channel == 1:
        hwgain = sdr._get_iio_attr("voltage1", "hardwaregain", False, sdr._ctrl)
    if channel == 2:
        hwgain = sdr._get_iio_attr("voltage0", "hardwaregain", False, sdr._ctrl_b)
    if channel == 3:
        hwgain = sdr._get_iio_attr("voltage1", "hardwaregain", False, sdr._ctrl_b)
    if channel == 4:
        hwgain = sdr._get_iio_attr("voltage0", "hardwaregain", False, sdr._ctrl_c)
    if channel == 5:
        hwgain = sdr._get_iio_attr("voltage1", "hardwaregain", False, sdr._ctrl_c)
    if channel == 6:
        hwgain = sdr._get_iio_attr("voltage0", "hardwaregain", False, sdr._ctrl_d)
    if channel == 7:
        hwgain = sdr._get_iio_attr("voltage1", "hardwaregain", False, sdr._ctrl_d)
    print(hwgain)
    assert hardwaregain_low <= hwgain <= hardwaregain_high


def harmonic_vals(classname, uri, channel, param_set, low, high, plot=False):
    """ harmonic_vals: Test first five harmonics and check to be within
        certain intervals. This test also requires a devices with TX and RX
        onboard where thetransmit signal can be recovered.Sinuoidal data is
        passed to DMAs, which is then estimated on the RX side.

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
            low: type=list
                List of minimum values for certain harmonics
            high: type=list
                List of maximum values for certain harmonics
            plot: type=boolean
                Boolean, if set the values are also plotted
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    for p in param_set.keys():
        setattr(sdr, p, param_set[p])

    time.sleep(3)

    N = 2 ** 15
    sdr.tx_cyclic_buffer = True
    sdr.tx_enabled_channels = [channel]
    sdr.tx_buffer_size = N * len(sdr.tx_enabled_channels)
    sdr.rx_enabled_channels = [channel]
    sdr.rx_buffer_size = N * len(sdr.rx_enabled_channels)

    ref = 2 ** 12

    if hasattr(sdr, "sample_rate"):
        RXFS = int(sdr.sample_rate)
    else:
        RXFS = int(sdr.rx_sample_rate)

    fc = RXFS * 0.1
    fc = int(fc / (RXFS / N)) * (RXFS / N)

    full_scale = 0.9
    ts = 1 / float(RXFS)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * ref * full_scale
    q = np.sin(2 * np.pi * t * fc) * ref * full_scale
    iq = i + 1j * q

    try:
        sdr.tx(iq)
        time.sleep(5)
        for _ in range(30):
            data = sdr.rx()
    except Exception as e:
        del sdr
        raise Exception(e)
    del sdr
    time.sleep(3)

    L = len(data)

    # ampl = 1 / L * np.absolute(fft(data))
    # ampl = 20 * np.log10(ampl / ref + 10 ** -20)

    # freqs = fftfreq(L, 1 / RXFS)

    ffampl, ffreqs = spec.spec_est(data, fs=RXFS, ref=2**12, num_ffts=2)

    # _, ml, hm, indxs = spec.find_harmonics_reduced(
    #     ffampl, ffreqs, num_harmonics=50, tolerance=0.01
    # )

    # _, ml, hm, indxs = spec.find_harmonics(
    #     ffampl, ffreqs, num_harmonics=7, tolerance=0.01
    # )

    _, ml, peaks, indxs = spec.find_harmonics_from_main(
        ffampl, ffreqs, RXFS, num_harmonics=4, tolerance=0.01
    )
    
    # sfdr, amp, freq, peaks, indxs = spec.sfdr(data, fs=RXFS, ref=2 ** 12, plot=False)
    # amp = fftshift(amp)
    # print("sfdr: ", sfdr)
    # print("Amps: ",amp)
    # print("Freqs: ", freq)
    if plot:
        import matplotlib.pyplot as plt

        plt.subplot(2, 1, 1)
        plt.plot(data, ".-")
        plt.plot(1, 1, "r.")
        plt.margins(0.1, 0.1)
        plt.xlabel("Time [s]")

        plt.subplot(2, 1, 2)
        plt.plot(ffreqs, ffampl)
        plt.plot(ffreqs[ml], ffampl[ml], "y.")
        plt.plot(ffreqs[indxs[0:3]], ffampl[indxs[0:3]], "y.")

        plt.margins(0.1, 0.1)
        plt.annotate("Fundamental", (ffreqs[ml], ffampl[ml]))
        plt.xlabel("Frequency [Hz]")
        plt.tight_layout()
        if channel == 1 or (classname == "adi.ad9364" and param_set["tx_rf_port_select"] == 'B'):
            k=1
        else:
            k=0
        plt.savefig("./results_log/graph" + str(k) + ".png")
        plt.close()
    assert low[0] <= ffampl[ml] <= high[0]
    for i in range(3):
        print("Harmonic should be between ", low[i+1], high[i+1])
        print("Harmonic is ", peaks[i])
        assert low[i+1] <= peaks[i] <= high[i+1]
        


def cyclic_buffer(uri, classname, channel, param_set):
    """cyclic_buffer: Construct Cyclic TX buffers and verify
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

    if hasattr(sdr, "sample_rate"):
        fs = int(sdr.sample_rate)
    else:
        fs = int(sdr.rx_sample_rate)

    N = 1024
    fc = -3000000
    fc = int(fc / (fs / N)) * (fs / N)
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
    """cyclic_buffer_exception: Construct Cyclic TX buffers and verify
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

    if hasattr(sdr, "sample_rate"):
        fs = int(sdr.sample_rate)
    else:
        fs = int(sdr.rx_sample_rate)

    N = 1024
    fc = -3000000
    fc = int(fc / (fs / N)) * (fs / N)
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
    """stress_context_creation: Repeatedly create and destroy a context

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
    """stress_rx_buffer_length: Repeatedly create and destroy buffers across different buffer sizes

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
    """stress_rx_buffer_creation: Repeatedly create and destroy buffers

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
    """stress_tx_buffer_creation: Repeatedly create and destroy TX buffers

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


def verify_underflow(uri, classname, channel, buffer_size, sample_rate):
    """verify_overflow: Verify overflow flags occur as expected

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        channel: type=list
            List of integers or list of list of integers of channels to
            enable through tx_enabled_channels
        buffer_size type=int
            List of buffer size to create and collect
        sample_rate=int
            Value to set sample rate of device in samples per second
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    TXFS = 1000
    N = buffer_size
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

    # Set low rate so we can keep up
    sdr.sample_rate = sample_rate
    # Clear status register
    sdr._rxadc.reg_write(0x80000088, 0x6)

    # Flush
    sdr.tx(d)
    for k in range(30):
        v = sdr._txdac.reg_read(0x80000088)
        if v & 1:
            sdr._txdac.reg_write(0x80000088, v)

    for _ in range(5):
        sdr.tx(d)
    v = sdr._txdac.reg_read(0x80000088)
    if v & 1:
        del sdr
        assert 0, "Unexpected underflow occurred"

    # Force an underflow
    sdr.tx(d)
    underflow_occured = False
    time.sleep(30)
    sdr.tx(d)
    for k in range(30):
        v = sdr._txdac.reg_read(0x80000088)
        if v & 1:
            underflow_occured = True
            sdr._txdac.reg_write(0x80000088, v)  # Clear

    del sdr
    assert underflow_occured, "No underflow occurred, but one was expected"


def verify_overflow(uri, classname, channel, buffer_size, sample_rate):
    """verify_overflow: Verify overflow flags occur as expected

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        channel: type=list
            List of integers or list of list of integers of channels to
            enable through tx_enabled_channels
        buffer_size type=int
            List of buffer size to create and collect
        sample_rate=int
            Value to set sample rate of device in samples per second
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    sdr.rx_enabled_channels = channel if isinstance(channel, list) else [channel]
    sdr.rx_buffer_size = 2 ** 20

    # Set low rate so we can keep up
    sdr.sample_rate = sample_rate
    # Clear status register
    sdr._rxadc.reg_write(0x80000088, 0x6)

    v = sdr._rxadc.reg_read(0x80000088)

    # Flush
    _ = sdr.rx()
    for k in range(100):
        v = sdr._rxadc.reg_read(0x80000088)
        if v & 4:
            # print(f"Overflow 1 {v} {k}")
            sdr._rxadc.reg_write(0x80000088, v)

    _ = sdr.rx()
    for k in range(30):
        v = sdr._rxadc.reg_read(0x80000088)
        if v & 4:
            del sdr
            assert 0, "Unexpected overflow occurred"

    # Force an overflow
    _ = sdr.rx()
    overflow_occured = False
    time.sleep(10)
    for k in range(30):
        v = sdr._rxadc.reg_read(0x80000088)
        if v & 4:
            overflow_occured = True
            sdr._rxadc.reg_write(0x80000088, v)  # Clear

    del sdr

    assert overflow_occured, "No overflow occurred, but one was expected"
