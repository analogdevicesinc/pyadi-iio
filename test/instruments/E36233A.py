import logging
import os

import pyvisa

if os.name == "nt":
    # Add Keysight IO Libraries to path
    KS_LIB_PATH = os.get.environ(
        "KS_LIB_PATH", r"C:\Program Files\Keysight\IO Libraries Suite\bin"
    )
    os.add_dll_directory(KS_LIB_PATH)


logging.basicConfig(level=logging.DEBUG)


class channel:
    def __init__(self, parent, channel_number):
        self.parent = parent
        self.channel_number = channel_number

    def _set_channel(self):
        self.parent._instr.write(f"INST CH{self.channel_number}")

    def _to_float(self, value):
        numbers = value.split("E")
        return float(numbers[0]) * pow(10, int(numbers[1]))

    @property
    def voltage(self):
        self._set_channel()
        v_temp = self.parent._instr.query("SOUR:VOLT?")
        return self._to_float(v_temp)

    @voltage.setter
    def voltage(self, value):
        self._set_channel()
        self.parent._instr.write(f"SOUR:VOLT {value}")

    @property
    def current(self):
        self._set_channel()
        i_temp = self.parent._instr.query("SOUR:CURR?")
        return self._to_float(i_temp)

    @current.setter
    def current(self, value):
        self._set_channel()
        self.parent._instr.write(f"SOUR:CURR {value}")

    @property
    def output_enabled(self):
        self._set_channel()
        return self.parent._instr.query("OUTP:STAT?")

    @output_enabled.setter
    def output_enabled(self, value):
        self._set_channel()
        value = 1 if value else 0
        self.parent._instr.write(f"OUTP:STAT {value}")

    @property
    def operational_mode(self):
        self._set_channel()
        return self.parent._instr.query("OUTP:PAIR?")

    @operational_mode.setter
    def operational_mode(self, value):
        self._set_channel()
        if value not in ["OFF", "SER", "PAR"]:
            raise Exception(f"Invalid operational mode. Must be one of: OFF, SER, PAR")
        self.parent._instr.write(f"OUTP:PAIR {value}")


class E36233A:
    id = "E36233A"
    num_channels = 2
    driver = "ktvisa32"

    """Keysight E36233A Power Supply"""

    def __init__(self, address=None, driver=None) -> None:
        """Initialize the instrument

        Args:
            address (str, optional): VISA address of the instrument. Defaults to autodiscovery.
            driver (str, optional): VISA driver to use. Defaults to ktvisa32.
        """
        if driver:
            self.driver = driver
        if not address:
            self._find_device()
        else:
            self.address = address
            self._instr = pyvisa.ResourceManager(self.driver).open_resource(
                self.address
            )
            idn = self._instr.query("*IDN?")
            if self.id not in idn:
                raise Exception(f"Device at {self.address} is not a {self.id}")

        self.ch1 = channel(self, 1)
        self.ch2 = channel(self, 2)

    def _find_device(self):
        """Find desired devices automatically"""

        rm = pyvisa.ResourceManager(self.driver)
        all_resources = rm.list_resources()
        for res in all_resources:
            logging.debug(f"Inspecting: {res}")
            idn = rm.open_resource(res).query("*IDN?")
            logging.debug(f"Found ID: {idn}")
            if self.id in idn:
                self.address = res
                self._instr = rm.open_resource(self.address)
                return
        raise Exception(f"No instrument found with ID: {self.id}")

    @property
    def reset(self):
        """Reset the instrument"""
        self._instr.write("*RST")


if __name__ == "__main__":
    inst = E36233A()
    print(inst.ch1.voltage)
