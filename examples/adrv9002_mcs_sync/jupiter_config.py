"""
This configuration file sets up the network parameters and hardware-specific settings for the
Jupiter SDR devices used in the system. Key parameters are specified such as transmit
frequency, amplitude and gain values for each channel as well as phased array antenna 
(used on Rx channels) parameters such as the distance between each antenna element 
relative to wavelength. Different values commented are given for testing the example with
a power splitter which requires lower gain settings.

Antennas setup (default):
Phased array antenna elements vs jupiter channels setup:
Rx1_primary  Rx2_primary  Rx1_secondary  Rx2_secondary
    Ch0          Ch1           Ch2            Ch3    -> rx_channels_used
Ant_elem_0   Ant_elem_1    Ant_elem_2     Ant_elem_3
    --------------- Polarization ------------------

                        air
       
    ^^^^^^^^^^^^^^^ Polarization ^^^^^^^^^^^^^^^^^^
                  Directional antenna
                    Tx1_primary

                    
Power splitter setup (uncomment settings for power splitter from jupiter_config.py):
Rx1_primary     Rx2_primary     Rx1_secondary   Rx2_secondary
    Ch0             Ch1             Ch2             Ch3    -> rx_channels_used
Out1_splitter   Out2_splitter   Out3_splitter   Out4_splitter
                        Splitter
                      In1_splitter
                       Tx1_primary
"""

# Set ip of the boards: one sychrona and two jupiters
# The primary board is the one transmitting in the examples
synchrona_ip = "10.48.65.206"
jupiter_ip_primary = "10.48.65.166"
jupiter_ip_secondary = "10.48.65.168"

# For Antennas setup (default):
# Below values were tested for 4 patch elements phased array antenna
# at receiver and one vivaldi antenna at transmitter
lo_freq = 5836000000 - 300000  # [Hz] LO frequency of jupiter
tx_sine_baseband_freq = 300000  # [Hz] Sine frequency trasnsmitted
amplitude_discrete = 2**14  # Discrete amplitude of transmitted samples
number_periods_sine_baseband = 12
lambda_over_d_spacing = 1.77  # for Rx phased array antenna
onboard_tx1_used = True
tx_channels_used = [0]  # Channels used to transmit
# Hardware Rx gain is automatically adjusted
# For manual hardware Rx gain control, replace with "spi"
rx_gain_control_mode = "automatic"
rx_gain = 34  # Hardware Rx gain control mode (affects gain only for "spi" control mode)
tx1_gain = 0 if onboard_tx1_used else -40  # 0 is maximum gain
tx2_gain = -40  # Very low gain on unused Tx channels
# Note: in some places in software, Ch1 drawn on Jupiter's black box is
# reffered as Ch0 (and Ch2 as Ch1)

# # For Power splitter setup:
# # Below values are used for testing with a power splitter ##########################
# lo_freq = 2200000000 - 40000 # LO frequency of jupiter
# tx_sine_baseband_freq = 40000 # Aine frequency transmitted
# amplitude_discrete = 2**14 # Discrete amplitude of transmitted samples
# number_periods_sine_baseband = 10
# lambda_over_d_spacing = 1.77
# onboard_tx1_used = True
# tx_channels_used = [0]
# rx_gain_control_mode = "spi"
# rx_gain = 20
# tx1_gain = -5 if onboard_tx1_used else -41 # 0 is maximum gain
# tx2_gain = -40 # Very low gain on unused Tx channels
######################################################################################

# The following variables are set automatically should not be modified
synchrona_ip = f"ip:{synchrona_ip}"
jupiter_ips = [jupiter_ip_primary, jupiter_ip_secondary]
jupiter_ips = [f"ip:{ip}" for ip in jupiter_ips]
rx_channels_used = [0, 1, 2, 3]
used_rx_channels = len(rx_channels_used)
for i in range(used_rx_channels):
    if len(rx_channels_used) < used_rx_channels:
        rx_channels_used.append(i)
    else:
        print("Warning: used_rx_channels is maximum 4, change config file!")
        print("Used rx channels: " + str(rx_channels_used))
# To modify sample rate, use another profile
sample_rate = 30720000  # [Hz] initialized with the profile used in examples
num_samps = int(
    (number_periods_sine_baseband * sample_rate) / tx_sine_baseband_freq
)  # Calculated number of samples per buffer
rx_buffer_size = num_samps  # Buffer size for one Rx capture
tx_buffer_size = num_samps  # Buffer size for one Tx tranmission
