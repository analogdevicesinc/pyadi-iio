import pyvisa
from pyvisa import constants
import time
import numpy as np

class N9000A:
    """
    Keysight N9000A / PXA Spectrum Analyzer Python Driver (PyVISA-based).
    """

    def __init__(self, resource_manager, resource_name):
        self.rm = resource_manager
        self.instr = self.rm.open_resource(resource_name)
        self.instr.timeout = 10000  # ms
        self.instr.encoding = 'utf-8'
        self.instr.write_termination = '\n'
        self.instr.read_termination = '\n'

    # -------------------------
    # Utility
    # -------------------------
    def write(self, cmd: str):
        self.instr.write(cmd)

    def query(self, cmd: str) -> str:
        return self.instr.query(cmd)

    def operation_complete(self):
        while True:
            if int(self.query('*OPC?')) == 1:
                break
            time.sleep(0.01)

    def reset(self):
        self.write('*RST')
        self.write('*CLS')
        self.operation_complete()

    # -------------------------
    # Local/Remote Mode
    # -------------------------
    def set_to_local_mode(self):
        self.write('SYST:LOC')

    def set_to_remote_mode(self):
        self.write('SYST:REM')

    # -------------------------
    # Frequency and Span
    # -------------------------
    def set_center_freq(self, freq_hz: float):
        self.write(f"FREQ:CENT {freq_hz}")

    def get_center_freq(self) -> float:
        return float(self.query("FREQ:CENT?"))

    def set_freq_span(self, span_hz: float):
        self.write(f"SENS:FREQ:SPAN {span_hz}")

    def get_freq_span(self) -> float:
        return float(self.query("SENS:FREQ:SPAN?"))

    # -------------------------
    # Bandwidth
    # -------------------------
    def set_resolution_bw(self, rbw_hz: float):
        self.write(f"BAND {rbw_hz}")

    def get_resolution_bw(self) -> float:
        return float(self.query("BAND?"))

    def set_resolution_bw_auto(self, enable=True):
        self.write(f"BAND:AUTO {'ON' if enable else 'OFF'}")

    # -------------------------
    # Instrument Modes
    # -------------------------
    def select_phase_noise_mode(self):
        self.write('INST:SEL PNOISE')

    def select_real_time_mode(self):
        self.write('INST:SEL RTSA')

    def select_spec_an_mode(self):
        self.write('INST:SEL SA')

    def select_iq_mode(self):
        self.write('INST:SEL BASIC')

    def select_iq_signal_ranging(self):
        self.write(':VOLTage:IQ:RANGe:AUTO ON')

    def select_iq_signal_data_format(self):
        self.write(':FORMat:BORDer NORMal')
        self.write(':FORMat:DATA REAL,32')

    def initiate_waveform_meas(self):
        self.write('*TRG')
        self.write(':INITiate:WAVeform')

    # -------------------------
    # IQ Data and Bandwidth
    # -------------------------
    def set_iq_mode_bandwidth(self, bandwidth_hz):
        if bandwidth_hz > 160e6:
            raise ValueError('Max bandwidth for IQ Mode is 160 MHz')
        self.write(f'SPEC:DIF:BAND {bandwidth_hz}')

    def get_iq_mode_bandwidth(self):
        return float(self.query('SPEC:DIF:BAND?'))

    def set_iq_spec_bandwidth(self, bandwidth_hz):
        self.write(f'SENS:SPEC:BAND {bandwidth_hz}')

    def get_iq_spec_bandwidth(self):
        return float(self.query('SENS:SPEC:BAND?'))

    def set_iq_spec_span(self, span_hz):
        self.write(f':SENS:SPEC:FREQ:SPAN {span_hz}')
    
    def get_iq_spec_span(self):
        return float(self.query(':SENS:SPEC:FREQ:SPAN?'))

    def fetch_iq_waveform(self):
        return self.query(':FETCH:WAV3?')

    def fetch_iq_data(self):                                #
        self.write(':FORMat:BORDer NORMal')
        self.write(':FORMat:DATA REAL,32')
        return self.query(':FETCH:WAV1?')

    def iq_measurement_data(self):
        return self.query(':READ:WAV0?')

    def iq_complex_data(self):
        self.write('CONF:SPEC:NDEF')
        returned_string = self.query('READ:SPEC0?')
        data = np.array([float(x) for x in returned_string.split(',')])
        in_phase = data[::2]
        quadrature = data[1::2]
        return in_phase + 1j * quadrature

    # -------------------------
    # Markers
    # -------------------------
    def marker_on(self, marker: int = 1):
        self.write(f"CALC:MARK{marker}:MODE POS")

    def marker_off(self, marker: int = 1):
        self.write(f"CALC:MARK{marker}:MODE OFF")

    def get_marker_power(self, marker: int = 1) -> float:
        return float(self.query(f"CALC:MARK{marker}:Y?"))

    def get_marker_freq(self, marker: int = 1) -> float:
        return float(self.query(f"CALC:MARK{marker}:X?"))

    def set_marker_freq(self, marker: int, freq_hz: float):
        self.write(f"CALC:MARK{marker}:X {freq_hz}")

    def set_marker_as_band_power(self, marker: int):
        self.write(f"CALC:MARK{marker}:FUNC BPOW")

    def set_band_span(self, marker: int, band_span_hz):
        self.write(f"CALC:MARK{marker}:FUNC:BAND:SPAN {band_span_hz}")

    # -------------------------
    # Attenuation and Preamp
    # -------------------------
    def set_attenuation(self, att_db):
        self.write(f"POW:ATT {att_db}")

    def set_attenuation_auto(self):
        self.write("POW:ATT:AUTO ON")

    def set_internal_preamp(self, state: str):
        self.write(f"POW:GAIN {state}")

    def set_internal_preamp_band(self, band: str):
        self.write(f"POW:GAIN:BAND {band}")

    def set_noise_floor_extension(self, state: str):
        self.write(f":SENS:CORR:NOIS:FLO {state}")

    # -------------------------
    # Sweep and Points
    # -------------------------
    def set_points(self, num_points):
        self.write(f"SWE:POIN {num_points}")

    def get_points(self):
        return int(self.query("SWE:POIN?"))

    def query_sweep_time(self):
        return float(self.query("SWE:TIME?"))

    def set_sweep_time(self, time_s):
        self.write(f":WAVeform:SWE:TIME {time_s}")

    def set_initiate_continuous_sweep(self, state: str):
        self.write(f"INIT:CONT {state}")

    def iq_trigger(self, state: str):
        self.write(':TRIGger:WAVeform:SOURce IMMediate')
        self.write(f':TRIGger:LINE:SLOPe {state}')

    # -------------------------
    # Spectrum Data
    # -------------------------
    def get_spectrum_data(self, pause_time=0.5):
        self.write('INIT:CONT OFF')
        self.write('INIT;*WAI')
        time.sleep(pause_time)
        while int(self.query('*OPC?')) == 0:
            time.sleep(0.01)
        returned_string = self.query('TRAC? TRACE1')
        power_values = [float(x) for x in returned_string.split(',')]
        start_freq = float(self.query('FREQ:START?'))
        stop_freq = float(self.query('FREQ:STOP?'))
        num_points = len(power_values)
        freq_values = np.linspace(start_freq, stop_freq, num_points)
        return freq_values, np.array(power_values)

    # -------------------------
    # Peak Table and Trace
    # -------------------------
    def set_peak_table(self, state: str):
        self.write(f'CALC:MARK:PEAK:TABL:STAT {state}')

    def set_peak_table_sort(self, sort: str):
        self.write(f'CALC:MARK:PEAK:SORT {sort}')

    def set_peak_table_display_line_value(self, value: str):
        self.write(f'DISP:WIND1:TRAC:Y:DLIN1 {value}')

    def set_peak_table_display_line_type(self, disp_line: str):
        self.write(f'CALC:MARK:PEAK:TABL:READ {disp_line}')

    def get_peak_table(self, thresh, excursion, sort, disp_line):
        self.set_peak_table_display_line_value(thresh)
        self.set_peak_table_sort(sort)
        self.set_peak_table_display_line_type(disp_line)
        self.trigger()
        returned_string = self.query(f'CALC:DATA:PEAK? {thresh}, {excursion}, {sort}, {disp_line}')
        returned_data = [float(x) for x in returned_string.split(',')]
        mag = returned_data[1::2]
        freq = returned_data[::2]
        return mag, freq

    def query_number_of_peaks(self):
        return int(self.query('TRAC:MATH:PEAK:POIN?'))

    def query_signal_peak_values(self):
        returned_string = self.query('TRAC:MATH:PEAK?')
        return np.array([float(x) for x in returned_string.split(',')])

    # -------------------------
    # Phase Noise
    # -------------------------
    def set_phase_noise_clear_trace(self, trace_num):
        self.write(f':TRACe:MONitor:CLEar TRACE{trace_num}')

    def set_phase_noise_reference_level(self, ref_level):
        self.write(f'DISP:LPL:VIEW:WIND:TRAC:Y:RLEV {ref_level}')

    def set_phase_noise_num_averages(self, num_avgs):
        self.write(f'MON:AVER:COUN {num_avgs}')

    def set_phase_noise_trace_type(self, trace_num, trace_type):
        self.write(f'TRAC{trace_num}:MON:TYPE {trace_type}')

    def set_phase_noise_decade_table_on_off(self, table_state):
        self.write(f'CALC:LPL:DEC:TABL {table_state}')

    def set_phase_noise_display_trace(self, trace_num, trace_state):
        self.write(f'TRAC{trace_num}:MON:DISP {trace_state}')

    def set_phase_noise_smoothing(self, num_smooths):
        self.write(f'LPL:SMO {num_smooths}')

    def set_phase_noise_turn_on_off_averaging(self, avg_state):
        self.write(f'MON:AVER {avg_state}')

    def set_phase_noise_adjust_atten_for_min_clip(self):
        self.write(':SENSe:POWer:RF:RANGe:OPTimize IMMediate')

    def set_phase_noise_start_freq(self, start_freq_hz):
        self.write(f':SENSe:LPLot:FREQuency:OFFSet:STARt {start_freq_hz}')

    def set_phase_noise_stop_freq(self, stop_freq_hz):
        self.write(f':SENSe:LPLot:FREQuency:OFFSet:STOP {stop_freq_hz}')

    def get_phase_noise_data(self):
        returned_string = self.query(':CALCulate:DATA3?')
        return np.array([float(x) for x in returned_string.split(',')])

    # -------------------------
    # Display Scaling
    # -------------------------
    def wavexscale(self, rlev, pdiv, rpos, autoscale):
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:X:RLEV {rlev} s')
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:X:PDIV {pdiv} ns')
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:X:RPOS {rpos}')
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:X:COUP {autoscale}')

    def waveyscale(self, rlev, pdiv, rpos, autoscale):
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:Y:RLEV {rlev} V')
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:Y:PDIV {pdiv} mV')
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:Y:RPOS {rpos}')
        self.write(f':DISP:SPEC:VIEW:WIND2:TRAC:Y:COUP {autoscale}')

    # -------------------------
    # FFT Window and Length
    # -------------------------
    def fftwindow(self, window):
        self.write(f':SENSe:SPEC:FFT:WIND {window}')

    def fftlen(self, length):
        self.write(f':SENSe:SPEC:FFT:LENG: {length}')

    def fftlenuk(self):
        return int(self.query(':SENSe:SPEC:FFT:LENG?'))

    # -------------------------
    # Reference Level
    # -------------------------
    def set_reference_level(self, ref_level, window_num=1):
        self.write(f':DISP:WIND{window_num}:TRAC:Y:RLEV {ref_level}')

    # -------------------------
    # Averaging
    # -------------------------
    def set_average_mode(self, state):
        self.write(f'TRAC:TYPE {state}')

    def set_number_averages(self, num_averages):
        self.write(f'AVER:COUN {num_averages}')

    # -------------------------
    # Abort
    # -------------------------
    def set_abort(self):
        self.write('ABOR')

    # -------------------------
    # Trigger
    # -------------------------
    def trigger(self):
        self.write('*TRG')

    # -------------------------
    # Miscellaneous
    # -------------------------
    def bursttrig(self, slope, delay, rellevel, abslevel):
        self.write(f':TRIG:SPEC:SEQ:SOUR RFB')
        self.write(f':TRIG:SEQ:RFB:SLOP {slope}')
        self.write(f'TRIG:SEQ:VID:DEL:STAT ON')
        self.write(f':TRIG:SEQ:RFB:DEL {delay} us')
        self.write(f':TRIG:SEQ:RFB:LEV:REL {rellevel} dB')
        self.write(f':TRIG:SEQ:RFB:LEV:ABS {abslevel} dBm')

    # def set_peak_table_display_line_value(self, value):
    #     self.write(f'DISP:WIND1:TRAC:Y:DLIN1 {value}')

    # def set_peak_table_display_line_type(self, disp_line):
    #     self.write(f'CALC:MARK:PEAK:TABL:READ {disp_line}')

    def set_continuous_peak_search(self, marker_num, state):
        self.write(f':CALC:MARK{marker_num}:CPS:STAT {state}')

    def set_peak_table_sort(self, sort):
        self.write(f'CALC:MARK:PEAK:SORT {sort}')

    def set_marker_as_band_power(self, marker_num):
        self.write(f'CALC:MARK{marker_num}:FUNC BPOW')

    def set_band_span(self, marker_num, band_span):
        self.write(f'CALC:MARK{marker_num}:FUNC:BAND:SPAN {band_span} MHz')

    def set_mech_attenuation_level(self, attenuation):
        self.write(f'POW:ATT {attenuation}')

    def attn_off_on(self, state):
        self.write(f'SENSe:POWer:RF:EATTenuation:STATe {state}')

    def set_internal_preamp(self, state):
        self.write(f'POW:GAIN {state}')

    def set_internal_preamp_band(self, state):
        self.write(f'POW:GAIN:BAND {state}')

    def set_noise_floor_extension(self, state):
        self.write(f':SENS:CORR:NOIS:FLO {state}')

    def set_reference_level(self, ref_level, window_num=1):
        self.write(f':DISP:WIND{window_num}:TRAC:Y:RLEV {ref_level}')

    def set_resolution_bandwidth(self, resolution_bandwidth):
        self.write(f'BAND {resolution_bandwidth} MHz')

    def get_resolution_bandwidth(self):
        return float(self.query('BAND?'))

    def set_resolution_bandwidth_to_auto(self):
        self.write('BAND:AUTO ON')

    def set_points(self, num_points):
        self.write(f'SWE:POIN {num_points}')

    def get_points(self):
        return int(self.query('SWE:POIN?'))

    def set_average_mode(self, state):
        self.write(f'TRAC:TYPE {state}')

    def set_peak_table(self, state):
        self.write(f'CALC:MARK:PEAK:TABL:STAT {state}')

    def query_sweep_time(self):
        return float(self.query('SWE:TIME?'))

    def set_sweep_time(self, time):
        self.write(f':WAVeform:SWE:TIME {time}')

    def set_initiate_continuous_sweep(self, state):
        self.write(f'INIT:CONT {state}')

    def set_continuous_peak_search(self, marker_num, state):
        self.write(f':CALC:MARK{marker_num}:CPS:STAT {state}')

    def set_abort(self):
        self.write('ABOR')

    def set_peak_table_sort(self, sort):
        self.write(f'CALC:MARK:PEAK:SORT {sort}')

    def get_peak_table(self, thresh, excursion, sort, disp_line):
        self.set_peak_table_display_line_value(thresh)
        self.set_peak_table_sort(sort)
        self.set_peak_table_display_line_type(disp_line)
        self.trigger()
        returned_string = self.query(f'CALC:DATA:PEAK? {thresh}, {excursion}, {sort}, {disp_line}')
        returned_data = [float(x) for x in returned_string.split(',')]
        mag = returned_data[1::2]
        freq = returned_data[::2]
        return mag, freq

    def query_number_of_peaks(self):
        return int(self.query('TRAC:MATH:PEAK:POIN?'))

    def query_signal_peak_values(self):
        returned_string = self.query('TRAC:MATH:PEAK?')
        return np.array([float(x) for x in returned_string.split(',')])

    def get_tone_power(self, freq_hz, rbw_hz=30e3, span_hz=1e6, marker=1, delay=0.35):
        prev_center = self.get_center_freq()
        prev_span = self.get_freq_span()
        prev_rbw = self.get_resolution_bw()

        self.marker_on(marker)
        self.set_continuous_peak_search(marker, 'ON')
        self.set_center_freq(freq_hz)
        self.set_freq_span(span_hz)
        self.set_resolution_bw(rbw_hz)

        time.sleep(delay)
        tone_pow = self.get_marker_power(marker)

        self.set_center_freq(prev_center)
        self.set_freq_span(prev_span)
        self.set_resolution_bw(prev_rbw)

        return tone_pow


# if __name__ == "__main__":
#     rm = pyvisa.ResourceManager()
#     resource = "TCPIP0::A-N9000A-30136.local::hislip0::INSTR"
#     sa = N9000A(rm, resource)

    # # Example: Get spectrum data
    # freqs, powers = sa.get_spectrum_data()
    # print("Frequencies:", freqs)
    # print("Powers:", powers)

    # # Example: Get tone power
    # power = sa.get_tone_power(10e9, rbw_hz=30e3, span_hz=160e6)
    # print(f"Tone power at 5.003 GHz: {power:.2f} dBm")