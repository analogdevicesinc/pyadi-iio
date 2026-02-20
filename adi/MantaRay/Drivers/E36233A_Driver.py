"""
PyVISA SCPI driver for Keysight E36233A DC Power Supply (single-channel).
Provides convenient wrappers for common SCPI commands.

Usage:
    from pyvisa import ResourceManager
    from adi.E36233A_Driver import E36233A

    rm = ResourceManager()
    ps = E36233A(rm, "TCPIP0::192.168.1.100::inst0::INSTR")
    print(ps.idn())
    ps.set_voltage(5.0)
    ps.set_current(0.5)
    ps.output_on()
    v = ps.measure_voltage()
    i = ps.measure_current()
    ps.output_off()
    ps.close()
"""
import time
import pyvisa


class E36233A:
    def __init__(self, resource_manager, resource_name, timeout_ms=5000):
        self.rm = resource_manager
        self.res = resource_name
        self.instr = self.rm.open_resource(resource_name)
        self.instr.timeout = int(timeout_ms)
        self.instr.encoding = "utf-8"
        self.instr.write_termination = "\n"
        self.instr.read_termination = "\n"

    # Low-level helpers
    def write(self, cmd: str):
        return self.instr.write(cmd)

    def query(self, cmd: str) -> str:
        return self.instr.query(cmd)

    def raw(self, cmd: str) -> str:
        """Send arbitrary SCPI. Returns response for queries, empty string for writes."""
        if cmd.strip().endswith("?"):
            return self.query(cmd)
        self.write(cmd)
        return ""

    # Identity / status
    def idn(self) -> str:
        return self.query("*IDN?")

    def reset(self):
        self.write("*RST")
        time.sleep(0.1)

    def clear(self):
        self.write("*CLS")

    def opc(self, timeout_s: float = 10.0) -> bool:
        """Block until operation complete (returns True on completion)."""
        self.write("*OPC")
        return self.query("*OPC?").strip() == "1"

    def system_error(self) -> str:
        return self.query("SYST:ERR?")

    # Remote / local
    def set_remote(self):
        self.write("SYST:REM")

    def set_local(self):
        self.write("SYST:LOC")

    # --- Convenience for channel addressing --------------------------------
    def _ch_addr(self, channel: int) -> str:
        """Address format for protection/status queries that accept (@n)."""
        return f"(@{int(channel)})"

    # Output control (dual channel device)
    def output_on(self, channel: int):
        self.write(f"OUTP ON,{self._ch_addr(channel)}")

    def output_off(self, channel: int):
        self.write(f"OUTP OFF,{self._ch_addr(channel)}")

    # def set_output(self, enable: bool):
    #     self.write(f"OUTP {'ON' if enable else 'OFF'}")

    # def output_state(self) -> bool:
    #     return bool(int(self.query("OUTP?")))

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

    # # Protection (OVP/OCP) - common SCPI forms for single-channel supplies
    # def set_ovp(self, volts: float):
    #     self.write(f"VOLT:PROT {float(volts)}")

    # def enable_ovp(self, enable: bool):
    #     self.write(f"VOLT:PROT:STAT {'ON' if enable else 'OFF'}")

    # def get_ovp(self) -> float:
    #     return float(self.query("VOLT:PROT?"))

    # def set_ocp(self, amps: float):
    #     self.write(f"CURR:PROT {float(amps)}")

    # def enable_ocp(self, enable: bool):
    #     self.write(f"CURR:PROT:STAT {'ON' if enable else 'OFF'}")

    # def get_ocp(self) -> float:
    #     return float(self.query("CURR:PROT?"))

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

    # Status queries
    def ovp_trip_status(self) -> bool:
        try:
            return bool(int(self.query("STAT:PROT:VOLT:TRIP?")))
        except Exception:
            return False

    def ocp_trip_status(self) -> bool:
        try:
            return bool(int(self.query("STAT:PROT:CURR:TRIP?")))
        except Exception:
            return False

    # Display / front panel
    def display_text(self, text: str):
        text = text[:64]
        self.write(f"DISP:TEXT '{text}'")

    # Utility
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
