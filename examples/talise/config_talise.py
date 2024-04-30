# Change for different applications
talise_address = ""  # add ip of talise
lo_freq = 1020000000 - 245760 # lo frequency of talise
tx_sine_baseband_freq = 245760 # sine frequency transmitted
amplitude_discrete = 2**14
lambda_over_d_spacing = 2
####################################

used_rx_channels = 4
rx_channels_used = [0, 1, 2, 3]
for i in range(used_rx_channels):
    if(used_rx_channels <= 4):
        rx_channels_used.append(i)
    else:
        print("Warning: used_rx_channels is maximum 4, change config file!")

tx_channels_used = [0]
rx_gain_control_mode = "manual"
rx_gain = 30#10
tx_gain = 0#-10 #maximum is 0dB
tx_unused_channel_gain = -80
sample_rate = 245760000 # Hz
num_samps = int((20*sample_rate)/tx_sine_baseband_freq) #int((20*sample_rate)/tx_sine_baseband_freq) # number of samples per call to rx()
rx_buffer_size = num_samps
tx_buffer_size = num_samps