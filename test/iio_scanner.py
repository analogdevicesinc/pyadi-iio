import os
import socket
import subprocess
import sys

import iio

import scapy.all as scapy

HOSTNAMES = ["analog.local", "analog.lan"]


def check_iio(address):
    try:
        return iio.Context("ip:" + address)
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
    if check_config(
        ctx, [device("ad9517"), device("ad9361-phy"), device("cf-ad9361-lpc", 2)]
    ):
        return "adrv9364"
    if check_config(
        ctx, [device("adm1177"), device("ad9361-phy"), device("cf-ad9361-lpc", 2)]
    ):
        return "pluto"
    if check_config(ctx, [device("ad9361-phy"), device("ad9361-phy-b")]):
        return "fmcomms5"
    if check_config(ctx, [device("ad9361-phy"), device("cf-ad9361-lpc", 2)]):
        return "ad9364"
    if check_config(ctx, [device("ad9361-phy"), device("cf-ad9361-lpc", 4)]):
        return "ad9361"

    if check_config(ctx, [device("axi-ad9144-hpc", 4), device("axi-ad9680-hpc", 2)]):
        return "daq2"

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


def scan_all():
    boards = []
    # Find USB/LOCAL
    ctxs = iio.scan_contexts()
    for ctx in ctxs:
        c = iio.Context(ctx)
        name = check_board_other(c)
        if name:
            boards.append(board(name, c.name))
    # FIND IP
    bs = ip_scan_auto()
    # bs = ip_scan("192.168.86")
    if bs not in boards:
        boards = boards + bs
    return boards


def find_device(name):
    for b in scan_all():
        if b.name == name:
            return (True, b)
    return (False, [])


if __name__ == "__main__":
    bs = scan_all()
    for b in bs:
        print(b.uri)
        print(b.name)
        print("---------")
