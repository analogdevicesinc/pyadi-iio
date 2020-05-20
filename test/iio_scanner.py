import os
import socket
import subprocess
import sys

import iio

import scapy.all as scapy

HOSTNAMES = [
    "analog.local",
    "analog.lan",
    "analog-zc706-daq2.local",
    "analog-zc706-fmcomms2.local",
]


def check_iio(address):
    try:
        return iio.Context("ip:" + address)
    except:
        return False


def check_iio_uri(uri):
    try:
        return iio.Context(uri)
    except:
        return False


def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))


def check_exist(address):
    arp_request = scapy.ARP(pdst=address)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    clients_list = []
    for element in answered_list:
        client_dict = {"ip": element[1].psrc, "mac": element[1].hwsrc}
        clients_list.append(client_dict)
    return clients_list


class device:
    def __init__(self, name, channels=[]):
        self.name = name
        self.channels = channels


class board:
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri


def check_config(ctx, devices):
    found = 0
    try:
        for dev in ctx.devices:
            for fdev in devices:
                if not dev.name:
                    continue
                if dev.name.lower() == fdev.name.lower():
                    if fdev.channels:
                        chans = 0
                        for chan in dev.channels:
                            chans = chans + chan.scan_element
                        found = found + (chans == fdev.channels)
                    else:
                        found = found + 1
        return found == len(devices)
    except:
        return False


def check_board_other(ctx):
    if check_config(
        ctx, [device("ad7291-ccbox"), device("ad9361-phy"), device("cf-ad9361-lpc", 4)]
    ):
        return "packrf"
    if check_config(
        ctx, [device("ad9517"), device("ad9361-phy"), device("cf-ad9361-lpc", 4)]
    ):
        return "adrv9361"

    if check_config(ctx, [device("ad7291-bob"), device("cf-ad9361-lpc", 2)]):
        return "adrv9364"

    if check_config(
        ctx, [device("adm1177"), device("ad9361-phy"), device("cf-ad9361-lpc", 2)]
    ):
        return "pluto"

    if check_config(
        ctx, [device("ad7291"), device("ad9361-phy"), device("cf-ad9361-lpc", 4)]
    ):
        return "fmcomms2"

    if check_config(
        ctx, [device("ad7291"), device("ad9361-phy"), device("cf-ad9361-lpc", 2),],
    ):
        return "fmcomms4"

    if check_config(ctx, [device("ad9361-phy"), device("ad9361-phy-b")]):
        return "fmcomms5"

    if check_config(ctx, [device("ad9361-phy"), device("cf-ad9361-lpc", 2)]):
        return "ad9364"

    if check_config(ctx, [device("ad9361-phy"), device("cf-ad9361-lpc", 4)]):
        return "ad9361"

    if check_config(ctx, [device("ad9166"), device("adf4372")]):
        return "cn0511"

    if check_config(ctx, [device("axi-ad9144-hpc", 4), device("axi-ad9680-hpc", 2)]):
        return "daq2"

    if check_config(ctx, [device("axi-ad9152-hpc", 2), device("axi-ad9680-hpc", 2)]):
        return "daq3"

    if check_config(ctx, [device("adrv9009-phy"), device("adrv9009-phy-b")]):
        return "adrv9009-dual"

    if check_config(ctx, [device("adrv9009-phy")]):
        return "adrv9009"

    if check_config(ctx, [device("ad9371-phy")]):
        return "ad9371"

    for dev in ctx.devices:
        if dev.name:
            return dev.name


def ip_scan_auto():
    boards = []
    addresses = []
    for host in HOSTNAMES:
        try:
            for ip in socket.gethostbyname_ex(host):
                if type(ip) == list and ip:
                    if ip[0] not in addresses:
                        addresses.append(ip[0])
        except:
            continue
    for address in addresses:
        ctx = check_iio(address)
        if ctx:
            name = check_board_other(ctx)
            b = board(name, "ip:" + address)
            if b not in boards:
                boards.append(b)
    return boards


def ip_scan(subnet):
    boards = []
    for ping in range(0, 255):
        address = subnet + "." + str(ping)
        res = check_exist(address)
        if res:
            ctx = check_iio(address)
            if ctx:
                print("ping to", address, "OK MAC", res[0]["mac"])
                name = check_board_other(ctx)
                boards.append(board(name, "ip:" + address))
    return boards


def scan_all(skip_usb=False):
    boards = []

    # FIND IP
    bs = ip_scan_auto()
    # bs = ip_scan("192.168.86")

    if bs not in boards:
        boards = boards + bs

    # Find USB/LOCAL
    if not skip_usb:
        ctxs = iio.scan_contexts()
        for ctx in ctxs:
            c = iio.Context(ctx)
            name = check_board_other(c)
            if name:
                if c.name == "local":
                    boards.append(board(name, "local:"))
                else:
                    boards.append(board(name, ctx))
    return boards


def get_device(uri):
    ctx = check_iio_uri(uri)
    if ctx:
        board_name = check_board_other(ctx)
        if board_name:
            if ctx.name == "local":
                b = board(board_name, "local:")
            else:
                b = board(board_name, uri)
        return b
    return None


def find_device(names, uri=None, config=None, ignore_skip=None):
    skip_usb = False
    if not isinstance(names, list):
        names = [names]
    if uri:
        b = get_device(uri)
        if b:
            boards = [b]
        else:
            return (False, [])
    elif config:
        # Convert config to board class
        boards = []
        for dev in config["uri-map"]:
            hardware_options = config["uri-map"][dev]
            for hardware in hardware_options.split(","):
                if not ignore_skip:  # Check if uri is actually valid
                    b = get_device(dev)
                    if not b:
                        continue
                    if b.name == hardware.strip():
                        print("Hardware matched")
                    else:
                        print("Not matched")
                        continue
                else:
                    b = board(hardware, dev)
                boards.append(b)

    else:
        boards = scan_all(skip_usb)

    for b in boards:
        for name in names:
            if b.name == name:
                return (True, b)

    return (False, [])


if __name__ == "__main__":
    bs = scan_all()
    for b in bs:
        print(b.uri)
        print(b.name)
        print("---------")
