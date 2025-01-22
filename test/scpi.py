import time
from test.eeprom import load_from_eeprom, save_to_eeprom
from tkinter.font import BOLD
from weakref import finalize

import iio
import numpy as np
import paramiko
import pytest
import pyvisa
from pyvisa import constants

import adi

supported_instruments = ["HAMEG Instruments,HM8123,5.12"]


def find_instrument():
    rm = pyvisa.ResourceManager()
    all_resources = rm.list_resources()
    if len(all_resources) == 0:
        return None
    for i in range(0, len(all_resources)):
        my_instrument = rm.open_resource(
            all_resources[i],
            baud_rate=9600,
            data_bits=8,
            parity=constants.Parity.none,
            stop_bits=constants.StopBits.one,
            write_termination="\r",
            read_termination="\r",
        )

        try:
            idn = my_instrument.query("*IDN?")
            if idn in supported_instruments:
                break
            else:
                print("This instrument is currently not supported!")
        except Exception as e:
            my_instrument = None
            continue
    return my_instrument


def select_channel(instr):
    idn = instr.query("*IDN?")
    if idn == "HAMEG Instruments,HM8123,5.12":
        ch = ["FRA", "FRB", "FRC"]
        for i in range(0, len(ch)):
            instr.write(ch[i])
            time.sleep(3)
            xmt = instr.query("XMT?")
            time.sleep(1)
            if xmt != "Not Available":
                return xmt


def get_freq(instr):
    # set gate time to 600 for better precision
    xmt = select_channel(instr)
    frq_str = xmt.split(" ", 2)
    scale = 1
    if frq_str[1] == "GHz":
        scale = pow(10, 9)
    elif frq_str[1] == "MHz":
        scale = pow(10, 6)
    elif frq_str[1] == "KHz":
        scale = pow(10, 3)
    return float(frq_str[0]) * scale


def get_clk_rate(classname, iio_uri):
    sdr = eval(classname + "(uri='" + iio_uri + "')")
    sdr._ctrl.debug_attrs["adi,clk-output-mode-select"].value = "1"
    sdr._ctrl.debug_attrs["initialize"].value = "1"

    full_uri = iio_uri.split(":", 2)
    if full_uri[0] != "ip":
        pytest.skip("Tuning currently supported only for ip URIs")
    ip = full_uri[1]

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="analog")
    dev = classname[4:]
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "cat /sys/kernel/debug/clk/" + dev + "_ext_refclk/clk_rate"
    )

    if ssh_stderr.channel.recv_exit_status() != 0:
        raise paramiko.SSHException("Command did not execute properly")

    clk_rate = ssh_stdout.readline()
    ssh_client.close()
    return float(clk_rate)


def dcxo_calibrate(classname, iio_uri):
    prev_diff = 0
    diff = 0
    finetune = False
    step = 1
    direction = -2

    # setting initial values at half the value from eeprom to make the tuning process faster
    coarse = 4
    fine = 4095

    instr = find_instrument()
    if instr is None:
        pytest.skip("No supported instrument found")
        return
    target_frq = get_clk_rate(classname, iio_uri)
    sdr = eval(classname + "(uri='" + iio_uri + "')")

    sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
    sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
    while 1:
        current_frq = get_freq(instr)

        prev_diff = diff
        diff = target_frq - current_frq
        if abs(round(diff)) < 20:
            print("Close to target value:", current_frq)
            break
        if direction == -2:
            direction = np.sign(diff)
        if finetune:
            step = int(round(-1 * diff / 2))
            if step == 0:
                step = -1 * direction
            fine += step
            fine = int(fine)
        else:
            if step != 0:
                if prev_diff != 0 and prev_diff != diff:
                    step = int(round(-1 * ((step * diff) / abs(diff - prev_diff)) / 2))
                coarse += step
            else:
                finetune = True

        sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
        sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)

        if coarse < 0 or coarse > 63 or fine < 0 or fine > 8191:
            pytest.fail("Outside tuning bounds")
            break

    save_to_eeprom(iio_uri, coarse, fine)
    # End clean
    del sdr
