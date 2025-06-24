import numpy as np
import re
import genalyzer as gn
import json
import os
import matplotlib.pyplot as plt
# Receieve data on AD9081
def data_capture(adc):
    adc.rx_destroy_buffer()
    for i in range(2): # setting this to range(4) helped with stale captures, maybe setting kernal buffer count to 1 will alleviate this
        # First data buffer clears/discard, second data buffer is used
        data = adc.rx()
    return data

def cal_capture(adc, phase_offsets):
    adc.rx_destroy_buffer()
    for i in range(2):
        data = adc.rx()
    data = cal_data(data,phase_offsets)
    return data    

# Add phasor with delay to complex data
# source: www.github.com/jonkraft
def phase_delayer(data, delay):
    # Adds phase delay in degrees
    delayed_data = data * np.exp(1j*np.deg2rad(delay))
    return delayed_data
 
def calc_dbfs(data):
    # calculates dBFS value of data for a 12 bit ADC
    NumSamples = len(data)
    win = np.hamming(NumSamples)
    y = data * win
    s_fft = np.fft.fft(y) / np.sum(win)
    s_shift = np.fft.fftshift(s_fft)
    s_dbfs = 20*np.log10(np.abs(s_shift)/(2**12))     # Pluto is a signed 12 bit ADC, so use 2^11 to convert to dBFS
    return s_dbfs

def cal_data(data, phaseCAL):
    for i in range(len(data)):
        data[i] = phase_delayer(data[i], phaseCAL[i])
    return data
 
def find_phase_delay(obj, adc, subarray_ref, delay_phases):
    enable_stingray_channel(obj,subarray_ref)
    data = np.array(data_capture(adc))
    cal_ant = []
    cal_ant.append(0)
    for i in range(len(data)-1):
        peak_sum = []
        for phase_delay in delay_phases:
            first_ant = phase_delayer(data[i], phase_delay*i+cal_ant[i])
            second_ant = phase_delayer(data[i+1], phase_delay*(i+1))
            delayed_sum = calc_dbfs(first_ant - second_ant)
            peak_sum.append(np.max(delayed_sum))
        null_val = np.min(peak_sum)
        null_index = np.where(peak_sum==null_val)
        cal_value = delay_phases[null_index]
        cal_ant.append(cal_value[0])
    disable_stingray_channel(obj,subarray_ref)
    return cal_ant

# Grab the element number on the ADAR1000 array
def strip_to_last_two_digits(input_string):
    # Find all sequences of digits in the string
    all_numbers = re.findall(r'\d+', input_string)
    # Join them together and take the last two digits
    last_two_digits = ''.join(all_numbers)[-2:]
    return last_two_digits

# Create dictionary with new_keys and array as the values
def create_dict(new_keys, array):
    result_dict = {}
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            result_dict[new_keys[i][j]] = array[i][j]
    return result_dict

def phase_digital(obj, adc, adc_ref, subarray_ref):
    """
    Measures calibrated phase offsets for AD9081 in units of milli-degrees.
    Returns digital phase offsets in a 1x4 row vector
    """
    # Enable analog array_reference channels for NCO calibration
    enable_stingray_channel(obj, subarray_ref)
    # Capture ADC data
    data = np.array(data_capture(adc))  
    # Extract sample 100 from each IQ, phase in degrees
    phase_compare = np.angle(data[:, 100], deg = True)
    # Measure phase delta with respect to reference and scale to millidegrees
    digital_phase_cal = (np.mod(phase_compare - phase_compare[adc_ref] + 180, 360) - 180) * 1e3
    # Disable analog array_reference channels
    disable_stingray_channel(obj, subarray_ref)
    # write NCO phases to AD9081
    adc.rx_main_nco_phases = (np.round(digital_phase_cal).astype(int)).tolist()
 
    return digital_phase_cal
 
def rx_gain(obj, adc, subarray):
    """
    Measures analog magnitude for Stingray to equalize amplitudes across all elements.
    Returns calibrated gain codes and magnitude in dBFS pre-calibration in an 8x4 matrix mapped to the Stingray elements.
    """
    element_map = np.array([[1, 5, 9, 13, 17, 21, 25, 29],
                 [2, 6, 10, 14, 18, 22, 26, 30],
                 [3, 7, 11, 15, 19, 23, 27, 31],
                 [4, 8, 12, 16, 20, 24, 28, 32]])
    adc_map = np.array([4,2,1,3])
    # Capture ADC data with initial gain, attenuation, and phase settings
    data = rx_single_channel_data(obj, adc, adc_map, subarray)
    # Measure analog magnitude pre-calibration
    analog_mag_pre_cal = get_analog_mag(data)
    # print("pre cal mag before reshape",analog_mag_pre_cal)
    analog_mag_pre_cal = np.reshape(analog_mag_pre_cal, np.shape(subarray), order = 'F')
    # print("pre cal mag after reshape", analog_mag_pre_cal)
    # Calculate gain codes and attenuation values based on pre-calibration magnitude
    gain_codes_cal, atten_cal = gain_codes(obj, analog_mag_pre_cal, "rx")
    # Create dictionary with new keys and values from array
    gain_dict = create_dict(element_map, gain_codes_cal)
    # print("gain dictionary:",gain_dict)
    atten_dict = create_dict(element_map, atten_cal)
    sorted_gain_dict = dict(sorted(gain_dict.items()))
    sorted_atten_dict = dict(sorted(atten_dict.items()))
    # print("sorted atten dict")
    # print(sorted_atten_dict)
    for element in obj.elements.values():
        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))
        element.rx_attenuator = sorted_atten_dict[value]
        #element.rx_attenuator = 0
        element.rx_gain = sorted_gain_dict[value]
        # print("channel:",value," has gain:", element.rx_gain)       
        obj.latch_rx_settings() # Latch SPI settings to devices
   
    # Capture ADC data with calibrated gain codes and attenuation values
    data = rx_single_channel_data(obj, adc, adc_map, subarray)
   
    # Measure analog magnitude post-calibration
    analog_mag_post_cal = get_analog_mag(data)
    analog_mag_post_cal = np.reshape(analog_mag_post_cal, np.shape(subarray), order = 'F')
    # print("mag pre cal:",analog_mag_pre_cal)
    # print("mag post cal:",analog_mag_post_cal)
    print(analog_mag_post_cal)
    return gain_codes_cal, atten_cal, analog_mag_pre_cal, analog_mag_post_cal
 
def wrap_to_360(angle):
    return angle % 360

def ind2sub(array_shape, index):
    rows = index % array_shape[0]
    cols = index // array_shape[0]
    return rows, cols

def phase_analog(sray_obj, adc_obj, adc_map, adc_ref, subarray_ref, subarray_targ,dig_phase):
    analog_phase = np.zeros((4, 8)) # Adjust the size as needed
    element_map = np.array([[1, 5, 9, 13, 17, 21, 25, 29],
                 [2, 6, 10, 14, 18, 22, 26, 30],
                 [3, 7, 11, 15, 19, 23, 27, 31],
                 [4, 8, 12, 16, 20, 24, 28, 32]])
    for ii in range(0, 2):
        for jj in range((subarray_targ.shape[1])):
            dummy_array = np.zeros((4, 8))
            if ii == 0:
                tmp_array_ref = subarray_ref[1]
                tmp_targ = subarray_targ[0, :]
                enable_stingray_channel(sray_obj, tmp_array_ref)
                enable_stingray_channel(sray_obj, tmp_targ[jj])
                row, col = ind2sub(dummy_array.shape, (tmp_targ[jj]-1))
        
            else:
                tmp_array_ref = subarray_ref[0]
                tmp_targ = subarray_targ[1:4]
                enable_stingray_channel(sray_obj, tmp_array_ref)
                enable_stingray_channel(sray_obj, tmp_targ[:,jj])
                row, col = ind2sub(dummy_array.shape, (tmp_targ[:,jj]-1))
                
            
            data = cal_capture(adc_obj,dig_phase)
            data = np.array(data).T

            phase_compare = np.angle(data[100, :]) * 180 / np.pi
            if ii == 0:
                #print(row, col)
                analog_phase[row, col] = wrap_to_360(phase_compare[adc_map[0]-1] - phase_compare[adc_map[1]-1])
            else:
                for n in range(len(adc_map)-1):
                    
                    analog_phase[row, col] = wrap_to_360(phase_compare[adc_map[n]-1] - phase_compare[adc_ref])
                    
                    #print(tmp_targ[:,jj])
                    #print(analog_phase)

            if ii == 0:
                disable_stingray_channel(sray_obj, tmp_targ[jj])
            else:
                disable_stingray_channel(sray_obj, tmp_targ[:,jj])    

        disable_stingray_channel(sray_obj, tmp_array_ref)
    analog_phase_dict = create_dict(element_map, analog_phase)
    for element in sray_obj.elements.values():
        str_channel = str(element)
        value = int(strip_to_last_two_digits(str_channel))
        element.rx_phase = analog_phase_dict[value]
        # print("channel:",value," has gain:", element.rx_gain)       
        sray_obj.latch_rx_settings() # Latch SPI settings to devices
    return analog_phase

def rx_single_channel_data(obj, adc, adc_map, array):
        """
        Captures single channel Rx data on a 1 channel per subarray basis.
        Returns raw ADC codes in a 32x4096 matrix.
        """
        rx_data = np.zeros((32,4096), dtype = complex)  # Allocate memory
        for a in range(np.size(array,1)):
            # Enable target channels
            enable_stingray_channel(obj, array[:,a])
            # Pull data from ADC
            data = np.array(data_capture(adc))
            data = data[:, :np.size(rx_data,1)] # remove data past 4096th column
            new_data = np.zeros((data.shape))
            for i in range(len(adc_map)):
                new_data[i] = data[adc_map[i]-1,:]

            for index, row in enumerate(array[:,a]):
                rx_data[row - 1,:] = new_data[index,:]
            # Disable target channels
            disable_stingray_channel(obj, array[:,a])
        return rx_data
 
def get_analog_mag(data):
    """
    get_analog_mag runs an FFT on the data to create a matrix of magnitudes.
    Help: dataADC codes is a 32x4096 matrix of raw ADC codes.
    Returns analog_mag which is a 1x32 row vector of magnitudes in dBFS.
    """
    analog_mag = np.zeros((1, np.size(data,0)))
   
    if data.ndim == 1:
        adc_fft_data = fft(data, False, "OneTone")
        analog_mag = adc_fft_data["A:mag_dbfs"]
    else:
        for i in range(np.size(data,0)):
            adc_fft_data = fft(data[i,:], False, "OneTone")
            analog_mag[0,i] = adc_fft_data['A:mag_dbfs']
           
    return analog_mag
 
def fft(complex_data, combined_waveforms, tone_type):
    """
    FFT on ADC sample domain waveform data
    """
    qres = 16 # padding out 12 bit ADC to 16 for FFT algorithm
    qres_grow = 18 # bit growth needed to accomadate combining 4 FFTs
    navg = 1
    nfft = 4096
    # Check if bit padding needed
    if combined_waveforms == True:
        qres = qres_grow
        data = complex_data
    elif combined_waveforms == False:
        qres = qres
        data = complex_data
    else:
        raise ValueError('combined_waveforms type unsupported. True or False are acceptable types.')
   
    real_data = data.real.astype(np.int64)
    imag_data = data.imag.astype(np.int64)
    tone_type = tone_type.lower()
    if tone_type == "twotone" and os.path.exists("rx_2tone.json"):
        try:
            with open('rx_2tone.json', 'r') as file:
                fft_settings = json.load(file)
        except FileNotFoundError:
            print("File not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
    elif tone_type == "onetone" and os.path.exists("rx_1tone.json"):
        try:
            with open('rx_1tone.json', 'r') as file:
                fft_settings = json.load(file)
        except FileNotFoundError:
            print("File not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
    else:
        raise ValueError('tone_type type unsupported. OneTone or TwoTone are acceptable types.')
        # Fourier analysis configuration
    #
    if file.name == "rx_1tone.json":
        key = "fa"
        gn.mgr_remove(key)
        gn.fa_create(key)
        gn.fa_load(file.name, key)
    else:
        raise AttributeError("Have not coded rx_2tone.json for genalyzer yet")
    # Do FFT analysis
 
    window = gn.Window.NO_WINDOW # window function to apply
    code_fmt = gn.CodeFormat.TWOS_COMPLEMENT # integer data format
    axis_type = gn.FreqAxisType.DC_CENTER # axis type
   
    fft_complex = gn.fft(real_data, imag_data, qres, navg, nfft, window, code_fmt)
    fft_results = gn.fft_analysis(key, fft_complex, nfft, axis_type)
 
    return fft_results
 
def gain_codes(obj, analog_mag_pre_cal, mode):
    """
    gainCodes  Determines Rx/Tx analog VGA gain codes for Stingray
    Help: returns calibrated gain codes and attenuation values.
    """
    atten = np.zeros(np.shape(analog_mag_pre_cal))
   
    # Polynomial fit coefficients for Rx and Tx modes
    if mode == "rx":
        poly_atten1 = [-4.178368227245296e-09, -3.124456767699238e-07, -7.218061870232358e-06,
                     1.146280656652001e-05, 0.003079353177989, 0.048281159204065,
                     0.247215102895886, 0.176811045216789, 10.163992861226674, 127.1237461140638]
        poly_atten0 = [4.12957161960063e-10, 1.11191262836380e-07, 1.34714959988008e-05,
                     0.000967813015434471, 0.0456701602403594, 1.47865205676699,
                     33.2281071820574, 510.768971360134, 5126.75849430329, 30268.0388934082, 79815.3362477404]
    elif mode == "tx":
        poly_atten1 = [2.11066024918707e-11, 5.70009839945272e-09, 5.49937839434060e-07,
                     2.73783996444945e-05, 0.000800103462132557, 0.0143895847100511,
                     0.159688022065331, 1.06808692792217, 4.50865732789487,
                     21.0313863981928, 127.541504127078]
        poly_atten0 = [5.00901188825329e-10, 1.44673726954726e-07, 1.86493751074489e-05,
                     0.00141263342869073, 0.0696128076080524, 2.33122230277517,
                     53.7090182591208, 840.244043642996, 8539.25517554357,
                     50904.6416796854, 135350.366810770]
        
    # Calculate delta in dB and convert delta to number of bits to subtract
    mag_min = np.min(analog_mag_pre_cal)
    mag_cal_diff = analog_mag_pre_cal - mag_min
    mag_post_cal = np.zeros((4,8))
    #gain_resolution = 23/127
    #for i in range(np.size(analog_mag_pre_cal)):
    #    mag_post_cal.flat[i] = np.round(127 - (mag_cal_diff.flat[i]/gain_resolution))
    
    mag_cal_poly = np.zeros(np.shape(analog_mag_pre_cal))
   
    # Find correct gain code values based on which polynomial should be used
    # Adjust attenuators accordingly
    for i in range(np.size(analog_mag_pre_cal)):
        if mag_cal_diff.flat[i] < 23:
            mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten1, -1 * mag_cal_diff.flat[i]))
        elif mag_cal_diff.flat[i] == np.inf:
            mag_cal_poly.flat[i] = 0
            atten.flat[i] = 1
        else:
            mag_cal_poly.flat[i] = np.floor(np.polyval(poly_atten0, -1 * mag_cal_diff.flat[i]))
            atten.flat[i] = 1
    mag_cal_poly = np.clip(mag_cal_poly, 0, 127)
    gain_codes_cal = mag_cal_poly
    
    print(gain_codes_cal)
    return gain_codes_cal, atten
 
def enable_stingray_channel(obj, elements=None, man_input=False):
    """
    Enables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn on (1-32): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 32]
    elements = elements.flatten()
    for device in obj.devices.values():
        if device.mode == "rx":
            for channel in device.channels:
                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))
                for elem in elements:
                    if elem == value:
                        channel.rx_enable = True
        elif device.mode == "tx":
            for channel in device.channels:
                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))
                for elem in elements:
                    if elem == value:
                        channel.pa_bias_on = -1.1
                        channel.tx_enable = True
        else:
            raise ValueError('Mode of operation must be either "rx" or "tx"')
 
def disable_stingray_channel(obj, elements=None, man_input=False):
    """
    Disables the specified Stingray channel based on the mode. If no elements are passed, ask for user input
    """
    if elements is None and man_input:
        user_input = input("Enter a comma-separated list of channels to turn off (1-32): ")
        elements = [int(x.strip()) for x in user_input.split(',') if 1 <= int(x) <= 32]
    elements = elements.flatten()
    for device in obj.devices.values():
        if device.mode == "rx":
            for channel in device.channels:
                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))
                for elem in elements:
                    if elem == value:
                        channel.rx_enable = False
        elif device.mode == "tx":
            for channel in device.channels:
                str_channel = str(channel)
                value = int(strip_to_last_two_digits(str_channel))
                for elem in elements:
                    if elem == value:
                        channel.tx_enable = False
        else:
            raise ValueError('Mode of operation must be either "rx" or "tx"')