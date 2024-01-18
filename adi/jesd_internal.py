# Copyright (C) 2020-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from .sshfs import sshfs


class eye_scan(object):
    _jesd_es_duration_ms = 100
    _jesd_prbs = 7

    _half_rate = {"mode": "Half Fate", "scale": 0.004}
    _quarter_rate = {"mode": "Quarter Rate", "scale": 0.001}

    lanes = {}

    def get_eye_data(self, lanes=None):
        """Get JESD204 eye scan data

        Args:
            lanes (list, optional): List of lanes to get data for. Defaults to None which will get data for all lanes.

        Returns:
            dict: Dictionary of lane data. Keys are lane numbers, values are dictionaries with keys "x", "y1", "y2", and "mode".
                where "x" is the x-axis data SPO, "y1" is the y-axis data for the first eye, "y2" is the y-axis data for the second eye,
                in volts

        """
        # Check if supported
        if "bist_2d_eyescan_jrx" not in self._ctrl.debug_attrs:
            raise Exception("2D eye scan not supported on platform")

        if not isinstance(lanes, list) and lanes is not None:
            lanes = [lanes]
        if lanes is None:
            if len(self.lanes) == 0:
                raise Exception("No lanes found. Please run find_lanes() first")
            lanes = list(self.lanes.keys())
        for lane in lanes:
            if lane not in self.lanes.keys():
                raise Exception(f"Lane {lane} not found.")

        lane_eye_data = {}

        for lane in lanes:
            # Configure BIST
            self._set_iio_debug_attr_str(
                "bist_2d_eyescan_jrx",
                f"{lane} {self._jesd_prbs} {self._jesd_es_duration_ms}",
            )

            eye_data = self._get_iio_debug_attr_str("bist_2d_eyescan_jrx_data")

            x = []
            y1 = []
            y2 = []

            for eye_line in eye_data.splitlines():
                if "#" in eye_line:
                    info = [int(s) for s in eye_line.split() if s.isdigit()]
                    if info[1] == 64:
                        mode = self._half_rate["mode"]
                        scale = self._half_rate["scale"]
                    else:
                        mode = self._quarter_rate["mode"]
                        scale = self._quarter_rate["scale"]
                    if info[0] != lane:
                        print("Invalid lane number for eye data")
                        print(f"Expected {lane}, got {info[0]}")
                else:
                    spo = [int(x) for x in eye_line.split(",")]
                    x.append(spo[0])
                    y1.append(spo[1] * scale)
                    y2.append(spo[2] * scale)

            graph_helpers = {
                "xlim": [-info[1] / 2, info[1] / 2 - 1],
                "xlabel": "SPO",
                "ylabel": "EYE Voltage (V)",
                "title": "JESD204 2D Eye Scan",
                "rate_gbps": info[2] / 1000000,
            }

            lane_eye_data[lane] = {
                "x": x,
                "y1": y1,
                "y2": y2,
                "mode": mode,
                "graph_helpers": graph_helpers,
            }

        return lane_eye_data


class jesd(eye_scan):
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
