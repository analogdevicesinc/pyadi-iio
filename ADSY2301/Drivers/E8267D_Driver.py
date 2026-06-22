import pyvisa
from pyvisa import constants
import time
import numpy as np

class E8267D():
    def __init__(self, resource_manager, resource_name):
        self.rm = resource_manager
        self.instr = self.rm.open_resource(resource_name)

    def set_to_local_mode(self):
        # SET_TOLOCALMODE Turn Sig Gen to local mode
        # You may need to implement a Python script to do this and keep the connection alive,
        # or simply close and reopen the connection.
        # Example: self.close_connection()
        pass

    def set_to_remote_mode(self):
        # SET_TOREMOTEMODE Turns the Sig Gen to remote mode
        # You may need to implement a Python script to do this without closing the session.
        pass

    def write(self, cmd: str):
        self.instr.write(cmd)

    def query(self, cmd: str) -> str:
        return self.instr.query(cmd)

    def set_freq_mhz(self, freq_mhz):
        # SET_FREQ_MHZ Sets the RF frequency (in MHz)
        self.write(f'FREQ {freq_mhz}MHz')

    def set_power_dbm(self, power_dbm):
        # SET_POWER_DBM Sets the RF output power (in dBm)
        self.write(f'POW {power_dbm}dBm')

    def set_output_state(self, state_str):
        # SET_OUTPUTSTATE Sets the RF output (ON/OFF)
        self.write(f'OUTP {state_str}')

    def set_two_tone_hz(self, freq_sep):
        # SET_TWOTONE_HZ Sets the Two Tone Space in Hz
        self.write(f'RAD:TTON:ARB:FSP {freq_sep}')

    def set_two_tone_align(self, align):
        # SET_TWOTONE_ALIGN Sets the alignment wrt to center frequency
        self.write(f'RAD:TTON:ARB:ALIG {align}')

    def set_two_tone_apply(self):
        # SET_TWOTONE_APPLY applies two tone settings.
        self.write('RAD:TTON:ARB:APP')

    def set_two_tone_state(self, state):
        # SET_TWOTONE_STATE enables or disables on/off of two tone generator.
        self.write(f'RAD:TTON:ARB:STAT {state}')
        self.write(f'OUTP:MOD:STAT {state}')

    def close(self):
        # CLOSE Override of BasicInstrument Close to turn off Sig Gen before closing the connection
        self.set_output_state('OFF')
        #super().close()

    def get_freq_hz(self, channel_num=1):
        # GET_FREQ_HZ Gets the frequency of the Sig Gen (Hz) for the given channel_num
        if channel_num != 1:
            freq = float(self.query(f'FREQ{str(channel_num)}?'))
        else:
            freq = float(self.query('FREQ?'))
        return freq

    def get_power_dbm(self, channel_num=1):
        # GET_POWER_DBM Gets the power of the Sig Gen (dBm) for the given channel_num
        if channel_num != 1:
            power = float(self.query(f'POW{str(channel_num)}?'))
        else:
            power = float(self.query('POW?'))
        return power

    def get_two_tone_hz(self, channel_num=1):
        # GET_TWOTONE_HZ Gets the two tone spacing of the Sig Gen (Hz) for the given channel_num
        if channel_num != 1:
            freq_spac = float(self.query(f'RAD:TTON:ARB:FSP{str(channel_num)}?'))
        else:
            freq_spac = float(self.query('RAD:TTON:ARB:FSP?'))
        return freq_spac

    def get_two_tone_align(self, channel_num=1):
        # GET_TWOTONE_ALIGN Gets the two tone alignment of the Sig Gen for the given channel_num
        if channel_num != 1:
            tton_align = self.query(f'RAD:TTON:ARB:ALIG{str(channel_num)}?')
        else:
            tton_align = self.query('RAD:TTON:ARB:ALIG?')
        return tton_align

    def get_two_tone_state(self, channel_num=1):
        # GET_TWOTONE_STATE Gets the two tone state (enabled/disabled) of the Sig Gen for the given channel_num
        if channel_num != 1:
            tton_en = self.query(f'RAD:TTON:ARB:STAT{str(channel_num)}?')
        else:
            tton_en = self.query('RAD:TTON:ARB:STAT?')
        return tton_en
