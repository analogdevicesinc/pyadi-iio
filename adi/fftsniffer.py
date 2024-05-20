"""FFT Sniffer Module for AD9084/AD9088"""

from adi.rx_tx import rx, attribute

def reset_buffer(func):
    """Wrapper for set calls to clear the buffer after setting a new value.
    """

    def wrapper(*args, **kwargs):
        if args[0]._rx:
            args[0]._rx.rx_destroy_buffer()
            args[0]._rx = None
        func(*args, **kwargs)

    return wrapper

class fftsniffer_rx(rx):
    _rx_channel_names = ["index", "voltage0_i", "voltage0_q", "magn0"]
    _skip_channel_order_check = True
    def __init__(self):
        pass

    def _super_init(self, rx_buffer_size=2**16):
        super().__init__(rx_buffer_size=rx_buffer_size)

class fftsniffer(attribute):
    """FFT Sniffer Class"""

    def __init__(self, fft_sniffer, ctx=None):
        self._fft_sniffer = fft_sniffer
        self._rx = None

    def capture_fft(self):
        """Capture FFT"""
        if not self._rx:
            self._rx = fftsniffer_rx()
            self._rx._rxadc = self._fft_sniffer
            self._rx._super_init(rx_buffer_size=self.fft_size)
            if self.fft_mode == "Magnitude":
                self._rx.rx_enabled_channels = [3]
            else:
                self._rx.rx_enabled_channels = [1, 2]
        if self.fft_mode == "Magnitude":
            return self._rx.rx()
        data = self._rx.rx()
        return data[0] + 1j * data[1]

    def get_bins_freq(self):
        """Get Bins Frequency"""
        bin_size = self.adc_sampling_rate_Hz / 512
        if self.real_mode:
            # 0 -> Fs/2
            return [bin_size * i for i in range(256)]
        # -Fs/2 -> Fs/2
        return [bin_size * i for i in range(-256, 256)]


    @property
    def fft_size(self):
        return 256 if self.real_mode else 512

    _fft_mode = "Magnitude"
    @property
    def fft_mode(self):
        """FFT Mode"""
        return self._fft_mode
    
    @fft_mode.setter
    @reset_buffer
    def fft_mode(self, value):
        if value in ["Complex", "Magnitude"]:
            self._fft_mode = value
        else:
            raise ValueError("Invalid FFT Mode. Choose 'Complex' or 'Magnitude'")
        self._fft_mode = value

    @property
    def real_mode(self):
        """Real Mode"""
        return self._get_iio_debug_attr("real_mode", self._fft_sniffer)
    
    @real_mode.setter
    @reset_buffer
    def real_mode(self, value):
        value = "1" if value else "0"
        self._set_iio_debug_attr_str("real_mode", value, self._fft_sniffer)

    @property
    def sorting_enable(self):
        """Sorting Enable"""
        v = self._get_iio_debug_attr("sort_enable", self._fft_sniffer)
        return v == "1" 

    @sorting_enable.setter
    @reset_buffer
    def sorting_enable(self, value):
        value = "1" if value else "0"
        self._set_iio_debug_attr_str("sort_enable", value, self._fft_sniffer)

    @property
    def continuous_mode(self):
        """Continuous Mode"""
        return self._get_iio_debug_attr("continuous_mode", self._fft_sniffer)
    
    @continuous_mode.setter
    @reset_buffer
    def continuous_mode(self, value):
        value = "1" if value else "0"
        self._set_iio_debug_attr_str("continuous_mode", value, self._fft_sniffer)

    @property
    def alpha_factor(self):
        """Alpha Factor"""
        return self._get_iio_debug_attr("alpha_factor", self._fft_sniffer)
    
    @alpha_factor.setter
    @reset_buffer
    def alpha_factor(self, value):
        self._set_iio_debug_attr_str("alpha_factor", value, self._fft_sniffer)

    @property
    def adc_sampling_rate_Hz(self):
        """ADC Sampling Rate"""
        return self._get_iio_debug_attr("adc_sampling_rate_Hz", self._fft_sniffer)
    

    @property
    def dither_enable(self):
        """Dither Enable"""
        return self._get_iio_debug_attr("dither_enable", self._fft_sniffer)
    
    @dither_enable.setter
    @reset_buffer
    def dither_enable(self, value):
        value = "1" if value else "0"
        self._set_iio_debug_attr_str("dither_enable", value, self._fft_sniffer)

    @property
    def delay_capture_ms(self):
        """Delay Capture"""
        return self._get_iio_debug_attr("delay_capture_ms", self._fft_sniffer)
    
    @delay_capture_ms.setter
    @reset_buffer
    def delay_capture_ms(self, value):
        self._set_iio_debug_attr_str("delay_capture_ms", value, self._fft_sniffer)

    @property
    def window_enable(self):
        """Window Enable"""
        return self._get_iio_debug_attr("window_enable", self._fft_sniffer)
    
    @window_enable.setter
    @reset_buffer
    def window_enable(self, value):
        value = "1" if value else "0"
        self._set_iio_debug_attr_str("window_enable", value, self._fft_sniffer)

    @property
    def bottom_fft_enable(self):
        """Bottom FFT Enable"""
        return self._get_iio_debug_attr("bottom_fft_enable", self._fft_sniffer)
    
    @bottom_fft_enable.setter
    @reset_buffer
    def bottom_fft_enable(self, value):
        value = "1" if value else "0"
        self._set_iio_debug_attr_str("bottom_fft_enable", value, self._fft_sniffer)

    @property
    def min_threshold(self):
        """Min Threshold"""
        return self._get_iio_debug_attr("min_threshold", self._fft_sniffer)
    
    @min_threshold.setter
    @reset_buffer
    def min_threshold(self, value):
        self._set_iio_debug_attr_str("min_threshold", value, self._fft_sniffer)

    @property
    def max_threshold(self):
        """Max Threshold"""
        return self._get_iio_debug_attr("max_threshold", self._fft_sniffer)
    
    @max_threshold.setter
    @reset_buffer
    def max_threshold(self, value):
        self._set_iio_debug_attr_str("max_threshold", value, self._fft_sniffer)

    @property
    def fft_enable_select(self):
        """FFT Enable Select"""
        return self._get_iio_debug_attr("fft_enable_sel", self._fft_sniffer)
    
    @fft_enable_select.setter
    @reset_buffer
    def fft_enable_select(self, value):
        self._set_iio_debug_attr_str("fft_enable_sel", value, self._fft_sniffer)

    @property
    def fft_hold_select(self):
        """FFT Hold Select"""
        return self._get_iio_debug_attr("fft_hold_sel", self._fft_sniffer)
    
    @fft_hold_select.setter
    @reset_buffer
    def fft_hold_select(self, value):
        self._set_iio_debug_attr_str("fft_hold_sel", value, self._fft_sniffer)
