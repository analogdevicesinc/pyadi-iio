import adi
import matplotlib.pyplot as plt
import pandas as pd
import re
import os.path
import collections
from fabric import Connection
import sys


class logger:
    def __init__(self, filename=""):
        self.filename = filename
        exists = os.path.exists(filename)
        if exists:
            self._log = pd.read_csv(filename, index_col=0)
        else:
            self._log = pd.DataFrame()

    def log(self, data, index=0):
        pddata = pd.DataFrame(data, index=[index])
        # self._log = pd.concat([self._log, pddata], axis=0)
        self._log = self._log.combine_first(pddata)
        self._log.update(pddata)

        # self._log.reset_index(inplace=True)
        # self._log= self._log.groupby(self._log.index)

        ##self._log = self._log.join(pddata, how = "left")
        # self._log.merge(pddata, left_index=True, right_index=True, how='outer', )
        # DataFrame.combine(self, other, func, fill_value=None, overwrite=True
        # func = lambda s1,s2: s2 if s2 else s1
        # self._log = self._log.combine(pddata, func)

    def save(self, filename=""):
        if not filename:
            filename = self.filename
            self._log.to_csv(filename)


def test1():
    return {"test_a": "1", "test_aa": "2"}


def test2():
    return {"test_b": "3", "test_bb": "4"}


class dmesg:
    def __init__(self, address):
        if "ip:" in address:
            address = address[3:]
        self.c = Connection(
            address,
            user="root",
            connect_kwargs={"password": "analog"},
            inline_ssh_env="?StrictHostKeyChecking=no&CheckHostIP=no&UserKnownHostsFile=/dev/null",
        )

    def get_dmesg(self, tail=0):
        tail_str = ""
        if tail:
            tail_str += "| tail -n " + str(tail)
        result = self.c.run("dmesg " + tail_str, hide="both")
        return result.stdout
        pass


class debug_adrv9009_zu11eg_fmcomms8:
    def __init__(self, fmcomms8="", jesd=None, dmesg=None):
        self.fmcomms8 = fmcomms8
        self.dmesg = dmesg
        self.jesd = jesd
        pass

    def _parse_str(self, data, str):
        str = str.replace(",", "\n")
        str = str.splitlines()
        for line in str:
            if not line:
                continue
            keyval = re.compile("( is )|(: )").split(line)
            # keyval=line.split(": ")
            key = keyval[0].strip()
            # we can parse val more here
            val = keyval[-1].strip()
            data[key] = val
        return data

    def _flatten(self, d, parent_key="", sep="_"):
        # https://stackoverflow.com/questions/6027558/flatten-nested-dictionaries-compressing-keys
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self._flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def get_flat_jesd_status(self, suffix=""):
        ret = self._flatten(self.jesd.get_all_statuses())
        return ret

    def get_flat_dmesg_status(self, tail=0, suffix=""):
        return {"dmesg" + suffix: self.dmesg.get_dmesg(tail=tail)}

    def get_flat_read_regs(self, suffix=""):
        return {
            "clock_chip_carrier_5a": fmcomms8._clock_chip_carrier.reg_read(0x5A),
            "clock_chip_attr": fmcomms8.trx_lo_chip_b,
        }

    pass


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage test.py <uri> <file.csv> <index>")
        exit(1)

    fmcomms_uri = sys.argv[1]
    fmcomms8_jesd = adi.jesd(fmcomms_uri)
    fmcomms8_dmesg = dmesg(fmcomms_uri)

    print("--Connecting to devices")
    log = logger(sys.argv[2])
    index = sys.argv[3]
    fmcomms8 = adi.adrv9009_zu11eg_fmcomms8(uri=fmcomms_uri)
    debug = debug_adrv9009_zu11eg_fmcomms8(
        fmcomms8, jesd=fmcomms8_jesd, dmesg=fmcomms8_dmesg
    )

    crash = False
    try:
        # fmcomms8.init()
        # fmcomms8.unsync()
        # fmcomms8.hmc7044_setup()
        # fmcomms8.clock_sync()

        fmcomms8.rx_enabled_channels = [0, 2, 4, 6]
        fmcomms8.rx_buffer_size = 2 ** 16

        # Configure LOs
        fmcomms8.trx_lo = 1000000000
        fmcomms8.trx_lo_chip_b = 1000000000
        fmcomms8.trx_lo_chip_c = 1000000000
        fmcomms8.trx_lo_chip_d = 1000000000

        fmcomms8.dds_single_tone(30000, 0.8)

        print("Getting data")
        # fmcomms8.mcs_chips()
        # fmcomms8.calibrate_rx_phase_correction()
        data = fmcomms8.rx_synced()
    except:
        crash = True
    log.log(debug.get_flat_jesd_status(), index)
    log.log(debug.get_flat_dmesg_status(tail=5), index)
    log.log({"crash": crash}, index)
    #    log.log ( {"buffer" : str(data[0][:100]) })

    plt.clf()
    plt.plot(data[0][:10000], label="Chan1 SOM A")
    plt.plot(data[1][:10000], label="Chan2 SOM A")
    plt.plot(data[2][:10000], label="Chan1 FMCOMMS")
    plt.plot(data[3][:10000], label="Chan2 FMCOMMS")
    plt.legend()
    plt.draw()
    plt.show()

    log.save()

    # run local - WIP
    # SUFFIX DEBUGS - TODO
    ## LOG EXCEPTIONS (?)  TODO
