# ADAR_functions.py

import pickle

import numpy as np

# MWT: probably better to pass verbosity to each function
verbose = True


def ADAR_init(beam):
    # Initialize the ADAR1000
    beam.reset()  # Performs a soft reset of the device (writes 0x81 to reg 0x00)
    beam._ctrl.reg_write(
        0x400, 0x55
    )  # This trims the LDO value to approx. 1.8V (to the center of its range)

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


def ADAR_update_Rx(beam):
    beam.latch_rx_settings()  # Loads Rx vectors from SPI.  Writes 0x01 to reg 0x28.


def ADAR_update_Tx(beam):
    beam.latch_tx_settings()  # Loads Tx vectors from SPI.  Writes 0x02 to reg 0x28.


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


# MWT: Consider combining Gainx into an array.
def ADAR_set_Taper(array, Gain1, Gain2, Gain3, Gain4, Gain5, Gain6, Gain7, Gain8):
    # print("element 1 gcal, val: ", gcal[0], ", ", int(Gain1 * gcal[0]))
    array.elements.get(1).rx_gain = int(Gain1 * 127 / 100 * gcal[0])
    # if Gainx=0, then also set the 20dB attenuator (set rx_attenuator to True)
    array.elements.get(1).rx_attenuator = not bool(Gain1)
    array.elements.get(2).rx_gain = int(Gain2 * 127 / 100 * gcal[1])
    array.elements.get(2).rx_attenuator = not bool(Gain2)
    array.elements.get(3).rx_gain = int(Gain3 * 127 / 100 * gcal[2])
    array.elements.get(3).rx_attenuator = not bool(Gain3)
    array.elements.get(4).rx_gain = int(Gain4 * 127 / 100 * gcal[3])
    array.elements.get(4).rx_attenuator = not bool(Gain4)
    array.elements.get(5).rx_gain = int(Gain5 * 127 / 100 * gcal[4])
    array.elements.get(5).rx_attenuator = not bool(Gain5)
    array.elements.get(6).rx_gain = int(Gain6 * 127 / 100 * gcal[5])
    array.elements.get(6).rx_attenuator = not bool(Gain6)
    array.elements.get(7).rx_gain = int(Gain7 * 127 / 100 * gcal[6])
    array.elements.get(7).rx_attenuator = not bool(Gain7)
    array.elements.get(8).rx_gain = int(Gain8 * 127 / 100 * gcal[7])
    array.elements.get(8).rx_attenuator = not bool(Gain8)
    array.latch_rx_settings()


# MWT: Consider combining phasex into an array.
def ADAR_set_Phase(
    array,
    PhDelta,
    phase_step_size,
    phase1,
    phase2,
    phase3,
    phase4,
    phase5,
    phase6,
    phase7,
    phase8,
):
    step_size = phase_step_size  # 2.8125
    array.elements.get(1).rx_phase = (
        (np.rint(PhDelta * 0 / step_size) * step_size) + phase1 + pcal[0]
    ) % 360
    array.elements.get(2).rx_phase = (
        (np.rint(PhDelta * 1 / step_size) * step_size) + phase2 + pcal[1]
    ) % 360
    array.elements.get(3).rx_phase = (
        (np.rint(PhDelta * 2 / step_size) * step_size) + phase3 + pcal[2]
    ) % 360
    array.elements.get(4).rx_phase = (
        (np.rint(PhDelta * 3 / step_size) * step_size) + phase4 + pcal[3]
    ) % 360
    array.elements.get(5).rx_phase = (
        (np.rint(PhDelta * 4 / step_size) * step_size) + phase5 + pcal[4]
    ) % 360
    array.elements.get(6).rx_phase = (
        (np.rint(PhDelta * 5 / step_size) * step_size) + phase6 + pcal[5]
    ) % 360
    array.elements.get(7).rx_phase = (
        (np.rint(PhDelta * 6 / step_size) * step_size) + phase7 + pcal[6]
    ) % 360
    array.elements.get(8).rx_phase = (
        (np.rint(PhDelta * 7 / step_size) * step_size) + phase8 + pcal[7]
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
    except:
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
    except:
        print("file not found, loading default (no phase shift)")
        return [0.0] * 8  # .append(0)  # if it fails load default value i.e. 0


gcal = load_gain_cal()
pcal = load_phase_cal()

if verbose == True:
    print("Gain cal: ", gcal)
    print("Phase cal: ", pcal)
