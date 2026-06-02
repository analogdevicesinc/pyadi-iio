import time
import numpy as np
import pyvisa


class E4440A:
    """
    Agilent / Keysight E4440A PSA Spectrum Analyzer driver (PyVISA-based).

    This version is trimmed to PSA-safe core spectrum-analyzer SCPI.
    Advanced measurement personalities / wideband digitizer features
    are intentionally not implemented here because they are option-dependent.
    """

    def __init__(self, resource_manager, resource_name, timeout_ms=10000):
        self.rm = resource_manager
        self.instr = self.rm.open_resource(resource_name)
        self.instr.timeout = timeout_ms
        self.instr.encoding = "utf-8"
        self.instr.write_termination = "\n"
        self.instr.read_termination = "\n"

    # -------------------------
    # Basic VISA / Utility
    # -------------------------
    def write(self, cmd: str):
        self.instr.write(cmd)

    def query(self, cmd: str) -> str:
        return self.instr.query(cmd).strip()

    def close(self):
        self.instr.close()

    def idn(self) -> str:
        return self.query("*IDN?")

    def options(self) -> str:
        """Returns installed option string, if supported by the instrument."""
        return self.query("SYST:OPT?")

    def operation_complete(self, sleep_s=0.01):
        while True:
            if int(self.query("*OPC?")) == 1:
                break
            time.sleep(sleep_s)

    def reset(self):
        self.write("*RST")
        self.write("*CLS")
        self.operation_complete()

    # -------------------------
    # Local / Remote
    # -------------------------
    def set_to_local_mode(self):
        self.write("SYST:LOC")

    def set_to_remote_mode(self):
        self.write("SYST:REM")

    # -------------------------
    # Frequency / Span
    # -------------------------
    def set_center_freq(self, freq_hz: float):
        self.write(f"FREQ:CENT {freq_hz}")

    def get_center_freq(self) -> float:
        return float(self.query("FREQ:CENT?"))

    def set_start_freq(self, freq_hz: float):
        self.write(f"FREQ:STAR {freq_hz}")

    def get_start_freq(self) -> float:
        return float(self.query("FREQ:STAR?"))

    def set_stop_freq(self, freq_hz: float):
        self.write(f"FREQ:STOP {freq_hz}")

    def get_stop_freq(self) -> float:
        return float(self.query("FREQ:STOP?"))

    def set_freq_span(self, span_hz: float):
        self.write(f"FREQ:SPAN {span_hz}")

    def get_freq_span(self) -> float:
        return float(self.query("FREQ:SPAN?"))

    # -------------------------
    # Amplitude / Reference / RF Front End
    # -------------------------
    def set_reference_level(self, ref_level_dbm: float, window_num: int = 1):
        self.write(f"DISP:WIND{window_num}:TRAC:Y:RLEV {ref_level_dbm}")

    def set_attenuation(self, att_db: float):
        self.write(f"POW:ATT {att_db}")

    def get_attenuation(self) -> float:
        return float(self.query("POW:ATT?"))

    def set_attenuation_auto(self, enable: bool = True):
        self.write(f"POW:ATT:AUTO {'ON' if enable else 'OFF'}")

    def set_internal_preamp(self, state: str):
        """
        state: typically 'ON' or 'OFF'
        """
        self.write(f"POW:GAIN {state}")

    # -------------------------
    # Resolution / Video Bandwidth
    # -------------------------
    def set_resolution_bw(self, rbw_hz: float):
        self.write(f"BAND {rbw_hz}")

    def get_resolution_bw(self) -> float:
        return float(self.query("BAND?"))

    def set_resolution_bw_auto(self, enable: bool = True):
        self.write(f"BAND:AUTO {'ON' if enable else 'OFF'}")

    def set_video_bw(self, vbw_hz: float):
        self.write(f"BAND:VID {vbw_hz}")

    def get_video_bw(self) -> float:
        return float(self.query("BAND:VID?"))

    def set_video_bw_auto(self, enable: bool = True):
        self.write(f"BAND:VID:AUTO {'ON' if enable else 'OFF'}")

    # -------------------------
    # Sweep / Trigger / Initiate
    # -------------------------
    def set_points(self, num_points: int):
        self.write(f"SWE:POIN {num_points}")

    def get_points(self) -> int:
        return int(self.query("SWE:POIN?"))

    def query_sweep_time(self) -> float:
        return float(self.query("SWE:TIME?"))

    def set_sweep_time(self, time_s: float):
        self.write(f"SWE:TIME {time_s}")

    def set_sweep_time_auto(self, enable: bool = True):
        self.write(f"SWE:TIME:AUTO {'ON' if enable else 'OFF'}")

    def set_initiate_continuous_sweep(self, state: str):
        """
        state: 'ON' or 'OFF'
        """
        self.write(f"INIT:CONT {state}")

    def initiate(self):
        self.write("INIT")

    def abort(self):
        self.write("ABOR")

    def trigger(self):
        self.write("*TRG")

    # -------------------------
    # Markers
    # -------------------------
    def marker_on(self, marker: int = 1):
        self.write(f"CALC:MARK{marker}:MODE POS")

    def marker_off(self, marker: int = 1):
        self.write(f"CALC:MARK{marker}:MODE OFF")

    def set_marker_freq(self, marker: int, freq_hz: float):
        self.write(f"CALC:MARK{marker}:X {freq_hz}")

    def get_marker_freq(self, marker: int = 1) -> float:
        return float(self.query(f"CALC:MARK{marker}:X?"))

    def get_marker_power(self, marker: int = 1) -> float:
        prev_cont = None
        try:
            self.set_initiate_continuous_sweep("OFF")
            self.initiate()
            self.operation_complete()
            return float(self.query(f"CALC:MARK{marker}:Y?"))
        finally:
            # best-effort restore
            self.set_initiate_continuous_sweep("ON")

    def peak_search(self, marker: int = 1):
        self.write(f"CALC:MARK{marker}:MAX")

    def next_peak(self, marker: int = 1):
        self.write(f"CALC:MARK{marker}:MAX:NEXT")

    def set_continuous_peak_search(self, marker: int, state: str):
        self.write(f"CALC:MARK{marker}:CPS:STAT {state}")

    def set_marker_as_band_power(self, marker: int):
        self.write(f"CALC:MARK{marker}:FUNC BPOW")

    def set_band_span(self, marker: int, band_span_hz: float):
        self.write(f"CALC:MARK{marker}:FUNC:BAND:SPAN {band_span_hz}")

    # -------------------------
    # Trace / Spectrum Data
    # -------------------------
    def get_spectrum_data(self, pause_time: float = 0.2):
        """
        Returns:
            freq_values (np.ndarray), power_values (np.ndarray)
        """
        self.write("INIT:CONT OFF")
        self.write("INIT;*WAI")
        time.sleep(pause_time)

        while int(self.query("*OPC?")) == 0:
            time.sleep(0.01)

        returned_string = self.query("TRAC? TRACE1")
        power_values = np.array([float(x) for x in returned_string.split(",")])

        start_freq = float(self.query("FREQ:STAR?"))
        stop_freq = float(self.query("FREQ:STOP?"))
        num_points = len(power_values)

        freq_values = np