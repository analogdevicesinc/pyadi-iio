"""
Comprehensive SCPI driver for Keysight N6705B (based on the official programming guide).
Provides high-level convenience methods covering common SCPI operations.

Usage:
    from pyvisa import ResourceManager
    from N6705B_FullDriver import N6705BFull

    rm = ResourceManager()
    ps = N6705BFull(rm, "TCPIP0::192.168.1.100::inst0::INSTR")
    print(ps.idn())
    ps.set_voltage(1, 3.3)
    ps.set_current(1, 1.0)
    ps.output_on(1)
    v = ps.measure_voltage(1)
    i = ps.measure_current(1)
    ps.close()
"""
import time
import pyvisa


class N6705B:
    def __init__(self, resource_manager, resource_name, timeout_ms=10000):
        self.rm = resource_manager
        self.res = resource_name
        self.instr = self.rm.open_resource(resource_name)
        self.instr.timeout = int(timeout_ms)
        self.instr.encoding = "utf-8"
        self.instr.write_termination = "\n"
        self.instr.read_termination = "\n"

    # --- Low level helpers -------------------------------------------------
    def write(self, cmd: str):
        """Send raw SCPI write (no response)."""
        return self.instr.write(cmd)

    def query(self, cmd: str) -> str:
        """Send raw SCPI query and return string response."""
        return self.instr.query(cmd)

    def ask(self, cmd: str) -> str:
        return self.query(cmd)

    def idn(self) -> str:
        return self.query("*IDN?")

    def reset(self):
        self.write("*RST")
        time.sleep(0.1)

    def clear(self):
        self.write("*CLS")

    def opc(self, timeout_s: float = 10.0) -> bool:
        self.write("*OPC")
        return self.query("*OPC?") == "1"

    def system_error(self) -> str:
        return self.query("SYST:ERR?")

    # --- Remote/local -----------------------------------------------------
    def set_remote(self):
        self.write("SYST:REM")

    def set_local(self):
        self.write("SYST:LOC")

    # --- Convenience for channel addressing --------------------------------
    def _ch_addr(self, channel: int) -> str:
        """Address format for protection/status queries that accept (@n)."""
        return f"(@{int(channel)})"

    # --- Output control ---------------------------------------------------
    def output_on(self, channel: int):
        self.write(f"OUTP ON,{self._ch_addr(channel)}")
        # print(f"OUTP ON,{self._ch_addr(channel)}")
    def output_off(self, channel: int):
        self.write(f"OUTP OFF,{self._ch_addr(channel)}")

    # def set_output(self, channel: int, enable: bool):
    #     self.write(f"OUTP{self._ch_addr(channel)}:STAT {'ON' if enable else 'OFF'}")

    # def output_state(self, channel: int) -> bool:
    #     return bool(int(self.query(f"OUTP{self._ch_addr(channel)}:STAT?")))

    # --- Source settings (voltage/current) --------------------------------
    def set_voltage(self, channel: int, volts: float):
        self.write(f"VOLT {volts}, {self._ch_addr(channel)}")
        # print((f"VOLT {volts}, {self._ch_addr(channel)}"))

    def set_current(self, channel: int, amps: float):
        self.write(f"CURR {amps}, {self._ch_addr(channel)}")

    def get_voltage_setting(self, channel: int) -> float:
        return float(self.query(f"VOLT? {self._ch_addr(channel)}"))

    def get_current_setting(self, channel: int) -> float:
        return float(self.query(f"CURR? {self._ch_addr(channel)}"))


    # --- Measurements -----------------------------------------------------
    def measure_voltage(self, channel: int) -> float:
        # Preferred explicit channel query form
        try:
            return float(self.query(f"MEAS:VOLT? {self._ch_addr(channel)}"))
        except Exception:
            return float(self.query("MEAS:VOLT?"))

    def measure_current(self, channel: int) -> float:
        try:
            return float(self.query(f"MEAS:CURR? {self._ch_addr(channel)}"))
        except Exception:
            return float(self.query("MEAS:CURR?"))

    def measure_power(self, channel: int) -> float:
        try:
            return float(self.query(f"MEAS:POW? {self._ch_addr(channel)}"))
        except Exception:
            return float(self.query("MEAS:POW?"))

    # Fetch more detailed measurement format if available
    def fetch_measurement(self, channel: int, meas_type: str = "VOLT") -> float:
        meas_cmd = meas_type.upper()
        return float(self.query(f"FETC:{meas_cmd}? {self._ch_addr(channel)}"))

    # --- Status and event registers ---------------------------------------
    def service_request_status(self) -> int:
        return int(self.query("STAT:OPER:ENAB?"))

    def event_summary(self) -> str:
        return self.query("STAT:SEM?")

    # --- Display and front panel ------------------------------------------
    def display_text(self, text: str):
        text = text[:64]
        self.write(f"DISP:TEXT '{text}'")

    # --- Memory / Save / Recall -------------------------------------------
    def save_state(self, slot: int = 1):
        self.write(f"MMEM:SAVE {int(slot)}")

    def recall_state(self, slot: int = 1):
        self.write(f"MMEM:LOAD {int(slot)}")

    # --- Calibration and self-test ----------------------------------------
    def self_test(self) -> str:
        return self.query("TST?")

    def calib_start(self):
        self.write("CAL:ALL")

    # --- Utility and raw command -----------------------------------------
    def raw(self, cmd: str) -> str:
        """Execute arbitrary SCPI command; return response if query."""
        if cmd.strip().endswith("?"):
            return self.query(cmd)
        else:
            self.write(cmd)
            return ""

    def close(self):
        try:
            self.instr.close()
        except Exception:
            pass

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()