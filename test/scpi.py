import time
from test.eeprom import load_from_eeprom, save_to_eeprom, save_to_eeprom_rate
from tkinter.font import BOLD
from weakref import finalize

import iio

import adi
import numpy as np
import paramiko
import pytest
import pyvisa
from pyvisa import constants

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
                pytest.skip("This instrument is currently not supported!")
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

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "cat /sys/kernel/debug/clk/ad9361_ext_refclk/clk_rate"
    )

    if ssh_stderr.channel.recv_exit_status() != 0:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "cat /sys/kernel/debug/clk/ad9361-refclk-gpio-gate/clk_rate"
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
    current_frq = 0
    # setting initial values at half the value from eeprom to make the tuning process faster
    coarse = 0  # table default for desired frequency is 8
    fine = 4000
    direction = 0  # coarse 0 -> higher value

    instr = find_instrument()
    if instr is None:
        pytest.skip("No supported instrument found")
        return
    target_frq = get_clk_rate(classname, iio_uri)
    if classname == "adi.FMComms5":
        save_to_eeprom_rate(iio_uri, target_frq)
        return

    sdr = eval(classname + "(uri='" + iio_uri + "')")

    try:
        sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
        sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
    except:
        frq_c0 = get_freq(instr)
        if abs(target_frq - frq_c0) > 5000:
            del sdr
            pytest.fail("Frequency is not in the appropriate range!")
            return
        else:
            del sdr
            return


    frq_c0 = get_freq(instr)
    coarse = 15
    sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
    frq_c15 = get_freq(instr)

    while 1:
        if (
            (frq_c0 > target_frq and frq_c15 < target_frq)
            or (frq_c0 < target_frq and frq_c15 > target_frq)
            or coarse == 63
        ):
            break
        else:
            coarse = coarse + 1
            sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
            frq_c0 = get_freq(instr)
            coarse = coarse + 15
            if coarse > 63:
                coarse = 63
            sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
            frq_c15 = get_freq(instr)

    if frq_c15 < frq_c0:
        frq_step = (frq_c0 - frq_c15) / 16
        direction = 0
    else:
        frq_step = (frq_c15 - frq_c0) / 16
        direction = 1
    if direction == 0:
        coarse = int((frq_c0 - target_frq) / frq_step)
    else:
        coarse = int((frq_c15 - target_frq) / frq_step)

    sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
    current_frq = get_freq(instr)

    while abs(target_frq - current_frq) > 80:
        if (target_frq > current_frq and direction == 0) or (
            target_frq < current_frq and direction == 1
        ):
            coarse = coarse - 1
            sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
            current_frq = get_freq(instr)
        else:
            coarse = coarse + 1
            sdr._set_iio_dev_attr("dcxo_tune_coarse", coarse, sdr._ctrl)
            current_frq = get_freq(instr)

    fine = 0
    sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
    frq_f0 = get_freq(instr)
    fine = 4000
    sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
    frq_fmax = get_freq(instr)
    if frq_f0 > frq_fmax:
        fine_step = (frq_f0 - frq_fmax) / 4001
        direction = 0
    else:
        fine_step = (frq_fmax - frq_f0) / 4001
        direction = 1
    if frq_f0 > target_frq:
        fine = int((frq_f0 - target_frq) / fine_step)
    else:
        fine = int((frq_fmax - target_frq) / fine_step)

    sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
    current_frq = get_freq(instr)

    while abs(target_frq - current_frq) > 5:
        if (target_frq > current_frq and direction == 0) or (
            target_frq < current_frq and direction == 1
        ):
            fine = fine - 5
            sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
            current_frq = get_freq(instr)
        else:
            fine = fine + 5
            sdr._set_iio_dev_attr("dcxo_tune_fine", fine, sdr._ctrl)
            current_frq = get_freq(instr)

    temp = sdr._get_iio_attr("temp0", "input", False)
    temp = int(temp / 1000)  # to get celsius value
    save_to_eeprom(iio_uri, coarse, fine, temp)
    # End clean
    del sdr
