# ADAR_functions.py

import pickle

import numpy as np

verbose = True


def ADAR_init(beam):
    beam.sequencer_enable = False
    beam.beam_mem_enable = False  # RAM control vs SPI control of the beam state, reg 0x38, bit 6.  False sets bit high and SPI control
    beam.bias_mem_enable = False  # RAM control vs SPI control of the bias state, reg 0x38, bit 5.  False sets bit high and SPI control
    beam.pol_state = False  # Polarity switch state, reg 0x31, bit 0. True outputs -5V, False outputs 0V
    beam.pol_switch_enable = (
        False  # Enables switch driver for ADTR1107 switch, reg 0x31, bit 3
    )
    beam.tr_source = "spi"  # TR source for chip, reg 0x31 bit 2.  'external' sets bit high, 'spi' sets bit low
    beam.tr_spi = (
        "rx"  # TR SPI control, reg 0x31 bit 1.  'tx' sets bit high, 'rx' sets bit low
    )
    beam.tr_switch_enable = True  # Switch driver for external switch, reg0x31, bit 4
    beam.external_tr_polarity = True  # Sets polarity of TR switch compared to TR state of ADAR1000.  True outputs 0V in Rx mode

    beam.rx_vga_enable = True  # Enables Rx VGA, reg 0x2E, bit 0.
    beam.rx_vm_enable = True  # Enables Rx VGA, reg 0x2E, bit 1.
    beam.rx_lna_enable = True  # Enables Rx LNA, reg 0x2E, bit 2.
    beam.rx_lna_bias_current = 8  # Sets the LNA bias to the middle of its range
    beam.rx_vga_vm_bias_current = 22  # Sets the VGA and vector modulator bias.


def ADAR_set_mode(beam, mode):
    if mode == "rx":
        # Configure the device for Rx mode
        beam.mode = (
            "rx"  # Mode of operation, bit 5 of reg 0x31. "rx", "tx", or "disabled"
        )
        # print("When TR pin is low, ADAR1000 is in Rx mode.")
        # beam._ctrl.reg_write(0x031, 180)   #Enables T/R switch control.  When TR is low, ADAR1000 is Rx mode
        SELF_BIASED_LNAs = True
        if SELF_BIASED_LNAs:
            beam.lna_bias_out_enable = False  # Allow the external LNAs to self-bias
        else:
            beam.lna_bias_on = -0.7  # Set the external LNA bias
        # Enable the Rx path for each channel
        for channel in beam.channels:
            channel.rx_enable = True


def ADAR_set_Taper(array, gainList):
    for index, element in enumerate(array.elements.values()):
        element.rx_gain = int(gainList[index] * 127 / 100 * gcal[index])
        element.rx_attenuator = not bool(gainList[index])
    array.latch_rx_settings()


def ADAR_set_Phase(array, PhDelta, phase_step_size, phaseList):
    for index, element in enumerate(array.elements.values()):
        element.rx_phase = (
            (np.rint(PhDelta * index / phase_step_size) * phase_step_size)
            + phaseList[index]
            + pcal[index]
        ) % 360
    array.latch_rx_settings()


def load_gain_cal(filename="gain_cal_val.pkl"):
    """ Load gain calibrated value, if not calibrated set all channel gain to maximum.
        parameters:
            filename: type=string
                      Provide path of gain calibration file
    """
    try:
        with open(filename, "rb") as file1:
            return pickle.load(file1)  # Load gain cal values
    except FileNotFoundError:
        print("file not found, loading default (all gain at maximum)")
        return [1.0] * 8  # .append(0x7F)


def load_phase_cal(filename="phase_cal_val.pkl"):
    """ Load phase calibrated value, if not calibrated set all channel phase correction to 0.
        parameters:
            filename: type=string
                      Provide path of phase calibration file
    """

    try:
        with open(filename, "rb") as file:
            return pickle.load(file)  # Load gain cal values
    except FileNotFoundError:
        print("file not found, loading default (no phase shift)")
        return [0.0] * 8  # .append(0)  # if it fails load default value i.e. 0


gcal = load_gain_cal()
pcal = load_phase_cal()

if verbose == True:
    print("Gain cal: ", gcal)
    print("Phase cal: ", pcal)
