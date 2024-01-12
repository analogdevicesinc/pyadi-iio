import pyvisa

import logging

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

    """Keysight E36233A Power Supply"""

    def __init__(self, address=None) -> None:
        if not address:
            self._find_device()
        else:
            self.address = address
            self._instr = pyvisa.ResourceManager().open_resource(self.address)
            if self._instr.query("*IDN?") != self.id:
                raise Exception(f"Device at {self.address} is not a {self.id}")

        self.ch1 = channel(self, 1)
        self.ch2 = channel(self, 2)

    def _find_device(self):
        """Find desired devices automatically"""

        rm = pyvisa.ResourceManager()
        all_resources = rm.list_resources()
        for res in all_resources:
            logging.debug(f"Inspecting: {res}")
            idn = rm.open_resource(res).query("*IDN?")
            logging.debug(f"Found ID: {idn}")
            if idn == self.id:
                self.address = res
                self._instr = rm.open_resource(self.address)
                return
        raise Exception(f"No instrument found with ID: {self.id}")

    @property
    def reset(self):
        """Reset the instrument"""
        self._instr.write("*RST")
