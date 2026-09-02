# Copyright (C) 2020-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from .sshfs import sshfs


class jesd:
    """JESD Monitoring"""

    def __init__(self, address, username="root", password="analog"):
        if "ip:" in address:
            address = address[3:]
        self.address = address
        self.username = username
        self.password = password
        self.rootdir = "/sys/bus/platform/devices/"

        # Connect
        self.fs = sshfs(address, username, password)

        self.find_jesd_dir()
        self.find_lanes()

    def find_lanes(self):
        self.lanes = {}
        for dr in self.dirs:
            if "-rx" in dr:
                self.lanes[dr] = []
                lanIndx = 0
                while 1:
                    li = "/lane{}_info".format(lanIndx)
                    if self.fs.isfile(self.rootdir + dr + li):
                        self.lanes[dr].append(li)
                        lanIndx += 1
                    else:
                        break

    def find_jesd_dir(self):
        dirs = self.fs.listdir(self.rootdir)
        self.dirs = []
        for dr in dirs:
            if "jesd" in dr:
                self.dirs.append(dr)

    def decode_status(self, status):
        status = status.replace(",", "\n")
        status = status.split("\n")
        link_status = {}
        for s in status:
            if ":" in s:
                o = s.split(":")
                link_status[o[0].strip().replace("/", "")] = o[1].strip()
            if "Link is" in s:
                link_status["enabled"] = s.split(" ")[-1].strip()

        return link_status

    def get_status(self, dr):
        return self.fs.gettext(self.rootdir + dr + "/status")

    def get_dev_lane_info(self, dr):
        return {
            ldir.replace("/", ""): self.decode_status(
                self.fs.gettext(self.rootdir + dr + "/" + ldir)
            )
            for ldir in self.lanes[dr]
        }

    def get_all_link_statuses(self):
        statuses = dict()
        for dr in self.dirs:
            if "-rx" in dr:
                statuses[dr] = self.get_dev_lane_info(dr)
        return statuses

    def get_all_statuses(self):
        return {dr: self.decode_status(self.get_status(dr)) for dr in self.dirs}
