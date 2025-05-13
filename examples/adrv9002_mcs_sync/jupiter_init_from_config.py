from time import sleep
import jupiter_config as config


def jupiter_init(sdrs):

    config.sample_rate = sdrs.rx0_sample_rate[0]
    # print("samp rate: " + str(config.sample_rate))

    config.num_samps = int(
        (config.number_periods_sine_baseband * config.sample_rate)
        / config.tx_sine_baseband_freq
    )  # calculated number of samples per buffer
    config.rx_buffer_size = config.num_samps
    config.tx_buffer_size = config.num_samps

    config.used_rx_channels = len(config.jupiter_ips) * 2
    config.rx_channels_used = []
    for i in range(config.used_rx_channels):
        config.rx_channels_used.append(i)

    # print("Transmitted baseband complex sinusoid frequency: " + str(config.tx_sine_baseband_freq))
    # print("Numeric value of discrete amplitude of transmitted signal: " + str(config.amplitude_discrete))
    sdrs.load_phase_cal()
    sdrs.load_gain_cal()
    if (config.used_rx_channels > 0) and (config.used_rx_channels <= 4):
        sdrs.num_rx_elements = config.used_rx_channels
    else:
        print("WARNING: Wrong number of used_rx_channels! Modify config file!")
        sdrs.num_rx_elements = 4

    # print("Number of samples per call to rx(): " + str(config.num_samps))

    sdrs.tx_destroy_buffer()
    sdrs.rx_destroy_buffer()
    # sleep(5)

    sdrs.rx_enabled_channels = config.rx_channels_used
    sdrs.tx_enabled_channels = config.tx_channels_used
    # for dev in [sdrs.primary] + sdrs.secondaries:
    #     print("dev.rx_enabled_channels: " + str(dev.rx_enabled_channels))
    #     print("dev.tx_enabled_channels: " + str(dev.tx_enabled_channels))

    sdrs.rx_ensm_mode_chan0 = "rf_enabled"
    sdrs.rx_ensm_mode_chan1 = "rf_enabled"

    # Config LOs
    sdrs.rx0_lo = config.lo_freq
    sdrs.rx1_lo = config.lo_freq
    sdrs.tx0_lo = config.lo_freq
    sdrs.tx1_lo = config.lo_freq
    # for dev in [sdrs.primary] + sdrs.secondaries:
    #     print("rx0_lo_freq: " + str(dev.rx0_lo))
    #     print("rx1_lo_freq: " + str(dev.rx1_lo))
    #     print("tx0_lo_freq: " + str(dev.tx0_lo))
    #     print("tx1_lo_freq: " + str(dev.tx1_lo))

    sdrs.gain_control_mode_chan0 = config.rx_gain_control_mode
    sdrs.gain_control_mode_chan1 = config.rx_gain_control_mode
    for dev in [sdrs.primary] + sdrs.secondaries:
        print("dev.gain_control_mode_chan0: " + str(dev.gain_control_mode_chan0))
        print("dev.gain_control_mode_chan1: " + str(dev.gain_control_mode_chan1))

    sdrs.tx_hardwaregain_all_chan0 = config.tx2_gain
    sdrs.tx_hardwaregain_all_chan1 = config.tx2_gain
    sdrs.primary.atten_control_mode_chan0 = "spi"
    sdrs.primary.tx_hardwaregain_chan0 = 0
    # print("sdrs.tx_hardwaregain_chan0: " + str(sdrs.tx_hardwaregain_chan0))
    # print("sdrs.tx_hardwaregain_all_chan0: " + str(sdrs.tx_hardwaregain_all_chan0))
    # print("sdrs.tx_hardwaregain_all_chan1: " + str(sdrs.tx_hardwaregain_all_chan1))

    if config.rx_gain_control_mode == "spi":
        sdrs.rx_hardwaregain_all_chan0 = config.rx_gain
        sdrs.rx_hardwaregain_all_chan1 = config.rx_gain
    #     print("sdrs.rx_hardwaregain_chan0: " + str(sdrs.rx_hardwaregain_chan0))
    #     print("sdrs.rx_hardwaregain_all_chan0: " + str(sdrs.rx_hardwaregain_all_chan0))

    sdrs.primary.tx_cyclic_buffer = True
    # print("sdrs.primary.tx_cyclic_buffer: " + str(sdrs.primary.tx_cyclic_buffer))

    for dev in [sdrs.primary] + sdrs.secondaries:
        dev.rx_buffer_size = config.num_samps
        dev._tx_buffer_size = config.num_samps
        # print("dev.rx_buffer_size: " + str(dev.rx_buffer_size))
        # print("dev._tx_buffer_size: " + str(dev._tx_buffer_size))
