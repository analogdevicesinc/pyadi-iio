import tkinter as tk
from datetime import date, datetime
from tkinter import Button, Entry, Label

import paramiko
import pytest


def save_to_eeprom(iio_uri, coarse, fine):
    full_uri = iio_uri.split(":", 2)
    if full_uri[0] != "ip":
        pytest.skip("Tuning currently supported only for ip URIs")
    ip = full_uri[1]

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="analog")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "find /sys/ -name eeprom"
    )
    eeprom_path = ssh_stdout.readline().rstrip("\n")

    if ssh_stderr.channel.recv_exit_status() != 0:
        raise paramiko.SSHException("find_eeprom command did not execute properly")

    this_day = date.today()
    if this_day.year <= 1995:
        pytest.skip(
            "System date and time not in order. Please connect the device to internet to update."
        )

    sn = popup_txt()

    hc = hex(coarse).lstrip("0x").rstrip("L")
    if coarse <= 16:
        hc = "0" + hc
    hf = hex(fine).lstrip("0x").rstrip("L")
    h = hc + hf

    cmd = (
        "fru-dump -i "
        + eeprom_path
        + " -o "
        + eeprom_path
        + " -s "
        + sn
        + " -d "
        + datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00")
        + " -t "
        + str(h)
        + " 2>&1"
    )
    sshin, sshout, ssherr = ssh_client.exec_command(cmd)
    if ssherr.channel.recv_exit_status() != 0:
        raise paramiko.SSHException("fru-dump command did not execute properly")

    ssh_client.close()


def popup_txt():
    popup = tk.Tk()
    popup.wm_title("Serial Number")
    label = Label(
        popup, text="Please write the serial number below:", font=("Verdana", 10)
    )
    tVar = tk.StringVar()
    label.pack(side="top", fill="x", pady=10)
    tb = Entry(popup, textvariable=tVar)
    tb.pack()
    btn = Button(popup, text="OK", command=popup.destroy)
    btn.pack()
    popup.mainloop()
    sn = tVar.get()
    if sn.isalnum():
        return sn
    else:
        pytest.skip("Invalid Serial Number")


def load_from_eeprom(iio_uri):
    full_uri = iio_uri.split(":", 2)
    if full_uri[0] != "ip":
        pytest.skip("Tuning currently supported only for ip URIs")
    ip = full_uri[1]

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username="root", password="analog")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "find /sys/ -name eeprom"
    )
    eeprom_path = ssh_stdout.readline().rstrip("\n")

    if ssh_stderr.channel.recv_exit_status() != 0:
        raise paramiko.SSHException("find_eeprom command did not execute properly")

    cmdin, cmdout, cmderr = ssh_client.exec_command(
        "fru-dump -i " + eeprom_path + " -b"
    )
    if cmderr.channel.recv_exit_status() != 0:
        raise paramiko.SSHException(
            "fru-dump board info command did not execute properly"
        )

    field = cmdout.readline()
    k = 0
    while field[:6] != "Tuning":
        field = cmdout.readline()
        k += 1
        # in case tuning parameters are not set, we shouldn't stay in the loop
        if k >= 20:
            print("No saved tuning values were found. Using defaults.")

    field = field[6:].lstrip(" \t: ")
    coarse = int("0x" + field[:2], 16)
    fine = int("0x" + field[2:], 16)
    return coarse, fine
