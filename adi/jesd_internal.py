# Copyright (C) 2020-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from .sshfs import sshfs


class jesd(object):
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
        if len(self.dirs) == 0:
            raise Exception("No JESD links found")
        for dr in self.dirs:
            if "-rx" in dr:
                self.lanes[dr] = []
                subdirs = self.fs.listdir(f"{self.rootdir}{dr}")
                for subdir in subdirs:
                    if "lane" in subdir and "info" in subdir:
                        if self.fs.isfile(f"{self.rootdir}{dr}/{subdir}"):
                            self.lanes[dr].append(subdir)

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


class jesd_eye_scan(jesd):
    _jesd_es_duration_ms = 10
    _jesd_prbs = 7
    _max_possible_lanes_index = 24

    _half_rate = {"mode": "Half Rate", "scale": 1}
    _quarter_rate = {"mode": "Quarter Rate", "scale": 4}

    lanes = {}

    def __init__(self, parent, address, username="root", password="analog"):
        """JESD204 Eye Scan

        Args:
            parent (adi.ad9081): Parent AD9081 instance
            address (str): IP address of the device
            username (str, optional): Username. Defaults to "root".
            password (str, optional): Password. Defaults to "analog".
        """
        super().__init__(address, username, password)
        self._parent = parent
        self._actual_lane_numbers = {}
        for device in self.lanes.keys():
            self._actual_lane_numbers[device] = self._get_actual_lane_numbers(device)

    def _get_actual_lane_numbers(self, device: str):
        """Get actual lane numbers from device

        The sysfs lanes always go 0-(N-1) where N is the number of lanes. But these
        are not always the actual lane numbers. This function gets the actual lane
        numbers from the device.
        """
        # Check if supported
        if "bist_2d_eyescan_jrx" not in self._parent._ctrl.debug_attrs:
            raise Exception("2D eye scan not supported on platform")

        if device not in self.lanes.keys():
            raise Exception(f"Device {device} not found.")
        num_lanes = len(self.lanes[device])

        actual_lane_numbers = []
        for lane_index in range(self._max_possible_lanes_index):
            try:
                self._parent._set_iio_debug_attr_str(
                    "bist_2d_eyescan_jrx",
                    f"{lane_index} {self._jesd_prbs} {self._jesd_es_duration_ms}",
                )
                actual_lane_numbers.append(str(lane_index))
                if len(actual_lane_numbers) == num_lanes:
                    break
            except OSError:
                continue

        if len(actual_lane_numbers) != num_lanes:
            raise Exception(
                f"Could not find all lanes for device {device}. Expected {num_lanes}, found {len(actual_lane_numbers)}."
            )

        return actual_lane_numbers

    def get_eye_data(self, device=None, lanes=None):
        """Get JESD204 eye scan data

        Args:
            device (str, optional): Device to get data for. Defaults to None which will get data for the first device found.
            lanes (list, optional): List of lanes to get data for. Defaults to None which will get data for all lanes.

        Returns:
            dict: Dictionary of lane data. Keys are lane numbers, values are dictionaries with keys "x", "y1", "y2", and "mode".
                where "x" is the x-axis data SPO, "y1" is the y-axis data for the first eye, "y2" is the y-axis data for the second eye,
                in volts

        """
        # Check if supported
        if "bist_2d_eyescan_jrx" not in self._parent._ctrl.debug_attrs:
            raise Exception("2D eye scan not supported on platform")

        if device is None:
            device = list(self._actual_lane_numbers.keys())[0]
        if device not in self._actual_lane_numbers.keys():
            raise Exception(f"Device {device} not found.")

        available_lanes = self._actual_lane_numbers[device]

        if not isinstance(lanes, list) and lanes is not None:
            lanes = [lanes]
        if lanes is None:
            if len(available_lanes) == 0:
                raise Exception("No lanes found. Please run find_lanes() first")
            lanes = available_lanes

        # Check if lanes are valid
        for lane in lanes:
            if lane not in available_lanes:
                raise Exception(f"Lane {lane} not found for device {device}.")

        # Enable PRBS on TX side
        devices_root = "/sys/bus/platform/devices/"
        dev_list = self.fs.listdir(devices_root)
        tx_dev = next((dev for dev in dev_list if "adxcvr-tx" in dev), None)
        if not tx_dev:
            raise Exception("No adxcvr-tx device found. Cannot enable PRBS.")

        self.fs.echo_to_fd("7", f"{devices_root}/{tx_dev}/prbs_select")

        lane_eye_data = {}

        print("Hold tight while we get the eye data...")

        for lane in lanes:
            # Configure BIST
            print(f"Getting eye data for lane {lane}")

            self._parent._set_iio_debug_attr_str(
                "bist_2d_eyescan_jrx",
                f"{lane} {self._jesd_prbs} {self._jesd_es_duration_ms}",
            )

            eye_data = self._parent._get_iio_debug_attr_str("bist_2d_eyescan_jrx")

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
                    if info[0] != int(lane):
                        print("Invalid lane number for eye data")
                        print(f"Expected {lane}, got {info[0]}")
                else:
                    spo = [float(x) for x in eye_line.split(",")]
                    x.append(spo[0])
                    y1.append(spo[1] * scale)
                    y2.append(spo[2] * scale)

            if len(x) == 0:
                raise Exception(f"No eye data found for lane {lane}.")

            graph_helpers = {
                "xlim": [-info[1] / 2, info[1] / 2 - 1],
                "ylim": [-256, 256],
                "xlabel": "SPO",
                "ylabel": "EYE Voltage (mV)",
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
