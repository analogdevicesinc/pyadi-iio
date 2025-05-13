"""Multi-chip synchronization for ADRV9002 transceivers across FPGAs"""

import logging

from .adrv9002 import adrv9002
from .context_manager import context_manager
from .attribute import attribute
from .sshfs import sshfs
from typing import List, Union
from threading import Thread
from time import sleep
import pickle
import sys

logger = logging.getLogger(__name__)


class ReturnableThread(Thread):
    # This class is a subclass of Thread that allows the thread to return a value.
    def __init__(self, target):
        Thread.__init__(self)
        self.target = target
        self.result = None

    def run(self) -> None:
        self.result = self.target()


class synchrona(attribute, context_manager):

    def __init__(self, uri="", _device_name=""):
        super().__init__(uri, _device_name)
        self._ctrl = self._ctx.find_device("hmc7044")
        if self._ctrl is None:
            raise Exception("No HMC7044 found")

    def sysref_request(self, value):
        self._set_iio_dev_attr("sysref_request", value, self._ctrl)

    sysref_request = property(None, sysref_request)


def _get_ctrl(ctrl, dev):
    if ctrl is None:
        return None
    _dev_ctrl = dev.ctx.find_device(ctrl.name)
    return _dev_ctrl


class map_to_multi_devices(object):
    """This class intercepts singleton attribute access
    and maps it to multiple devices"""

    _enable_interception = True

    @property
    def _devices(self):
        return [self.primary] + self.secondaries

    # Intercept methods
    def _set_iio_dev_attr_str(self, attr, val, _ctrl=None):
        for dev in self._devices:
            logger.debug(f"Setting {attr} on {dev.uri}")
            dev._set_iio_dev_attr_str(attr, val, _get_ctrl(_ctrl, dev))

    def _get_iio_dev_attr_str(self, attr, _ctrl=None):
        return [
            dev._get_iio_dev_attr_str(attr, _get_ctrl(_ctrl, dev))
            for dev in self._devices
        ]

    def _set_iio_dev_attr(self, attr, val, _ctrl=None):
        for dev in self._devices:
            logger.debug(f"Setting {attr} on {dev.uri}")
            dev._set_iio_dev_attr(attr, val, _get_ctrl(_ctrl, dev))

    def _get_iio_dev_attr(self, attr, _ctrl=None):
        return [
            dev._get_iio_dev_attr(attr, _get_ctrl(_ctrl, dev)) for dev in self._devices
        ]

    def _set_iio_attr(self, channel, attr, output, val, _ctrl=None):
        for dev in self._devices:
            logger.debug(f"Setting {attr} on {dev.uri}")
            dev._set_iio_attr(channel, attr, output, val, _get_ctrl(_ctrl, dev))

    def _get_iio_attr_str(self, channel, attr, output, _ctrl=None):
        return [
            dev._get_iio_attr_str(channel, attr, output, _get_ctrl(_ctrl, dev))
            for dev in self._devices
        ]

    def _get_iio_attr(self, channel, attr, output, _ctrl=None):
        return [
            dev._get_iio_attr(channel, attr, output, _get_ctrl(_ctrl, dev))
            for dev in self._devices
        ]

    def rx_destroy_buffer(self):
        """rx_destroy_buffer: Clears RX buffer"""
        for dev in self._devices:
            logger.debug(f"Destroying RX buffer on {dev.uri}")
            dev.rx_destroy_buffer()

    def tx_destroy_buffer(self):
        """tx_destroy_buffer: Clears TX buffer"""
        for dev in self._devices:
            logger.debug(f"Destroying TX buffer on {dev.uri}")
            dev.tx_destroy_buffer()


class adrv9002_multi(map_to_multi_devices, adrv9002):

    primary = None
    secondaries = []
    enable_ssh = False

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("adi.adrv9002_multi")
    logger.setLevel(logging.DEBUG)
    logger = logging.getLogger("paramiko")
    logger.setLevel(logging.CRITICAL)

    def __init__(
        self,
        primary_uri="ip:analog.local",
        secondary_uris=[],
        sync_uri="ip:synchrona.local",
        enable_ssh=False,
        sshargs=None,
        profile_path="",
    ):

        self.enable_ssh = enable_ssh
        # application level calibration attributes
        self.num_cal_elements = 4
        self.pcal_data = [0.0 for i in range(0, (self.num_cal_elements - 1))]
        self.gcal_data = [0.0 for i in range(0, (self.num_cal_elements - 1))]

        # Mirror top level design off single device
        adrv9002.__init__(self, uri=primary_uri)

        # Reuse context for primary
        class adrv9002_primary(adrv9002):
            def __init__(self, ctx, uri) -> None:
                super().__init__(uri)
                self._ctx = ctx
                self.uri = uri

        logger.debug(f"Creating primary device: {primary_uri}")
        self.primary = adrv9002_primary(self.ctx, primary_uri)
        self.secondaries = []
        for uri in secondary_uris:
            logger.debug(f"Creating secondary device: {uri}")
            self.secondaries.append(adrv9002(uri=uri))

        self.sync = synchrona(uri=sync_uri)

        self._dma_show_arming = False
        self._jesd_show_status = False
        self._jesd_fsm_show_status = False
        self._clk_chip_show_cap_bank_sel = False
        self._resync_tx = False
        self._rx_initialized = False
        self._request_sysref_carrier = False

        if enable_ssh:
            self.primary_ssh = sshfs(address=primary_uri, **sshargs)
            self.secondaries_ssh = [
                sshfs(address=uri, **sshargs) for uri in secondary_uris
            ]
            # self.sync_ssh = sshfs(address=sync_uri, **sshargs)

        # Check if we have a single device or
        # multiple devices
        REBOOT = False
        if ([primary_uri] + secondary_uris) == 1:
            internal_mcs = True
        else:
            internal_mcs = False

        # Check reboot if necessary
        if REBOOT:
            print("Rebooting all systems")
            for dev in [self.primary_ssh] + self.secondaries_ssh:
                dev._run("reboot")
            sys.exit(0)

        # Initialize profile
        # ADRV9002 stuff
        if profile_path != "":
            print("Loading profiles: " + profile_path)
            self.write_profile(profile_path)
        else:
            logger.warning("No profile path provided, skipping profile loading")

        # Setup MCS
        self.__setup_mcs(internal_mcs)
        print("Custom ADRV9002 system initialized")

    def __setup_mcs(self, internal_mcs):
        # For one system, the MCS sync is done automatically by the kernel driver
        # after a profile is loaded.
        # The "one system only" info is defined in the devicetree, loaded at boot.
        if internal_mcs:
            print("MSC not required")
        else:
            self.primary.ctx.set_timeout(30000)
            for sdr in self.secondaries:
                sdr._ctx.set_timeout(30000)

            # The linux driver exposes the "multi_chip_sync" attribute, which is a bit
            # more special. To know that the MCS was done successfully, one has to wait
            # for the multi_chip_sync attribute setting process to end successfully.
            # The attribute setting of multi_chip_sync only ends after MCS procedure is
            # completed or timeout occurs.
            # For the MCS sync to end, the adrv9002 needs to receive the 6 MCS pulse train.
            # In other words, we need to configure(put in MCS state) each adrv9002
            # in a separate thread, send the 6 MCS pulse train and wait for all started
            # threads that have put the adrv9002 devices in MCS state to end in success.

            mcs_threads = {}
            for dev in self._devices:
                print(f"Setting up MCS for {dev.uri}")
                mcs_threads[dev.uri] = ReturnableThread(
                    target=lambda: dev._set_iio_dev_attr("multi_chip_sync", "1")
                )
                mcs_threads[dev.uri].start()

            sleep(1)
            print("Waiting for 6 pulses")

            ############################################################################
            # 2 Issue sync pulse
            # MCS request
            for t in range(6):
                try:
                    print("Requesting sysref")
                    self.sync.sysref_request = 1
                    break
                except Exception as e:
                    if t == 5:
                        raise Exception("Failed to request sysref")
                    print(e)
                    sleep(0.1)

            # Wait for mcs done
            for dev in self._devices:
                while mcs_threads[dev.uri].is_alive():
                    print("Waiting for MCS done on" + dev.uri)
                    sleep(0.5)

            print("Mute DAC data sources")
            self.mute_dac_data_sources()

    def __del__(self):
        # self.primary.__del__()
        for secondary in self.secondaries:
            secondary.__del__()
        if self.enable_ssh:
            for secondary in self.secondaries_ssh:
                secondary.__del__()
        # self.sync.__del__()

    def _run(self, cmd):
        output = {}
        errors = {}
        for ssh_dev in [self.primary_ssh] + self.secondaries_ssh:
            o, e = ssh_dev._run(cmd)
            output[ssh_dev.address] = o
            errors[ssh_dev.address] = e

        return output, errors

    def rx_arm(self):
        logger.debug("ARM RX transfer path")
        for dev in [self.primary] + self.secondaries:
            dev._rxadc.reg_write(0x80000048, 0x2)

    def tx_arm(self):
        logger.debug("ARM RX transfer path")
        for dev in [self.primary] + self.secondaries:
            dev._txdac.reg_write(0x80000044, 0x2)

    def rx(self):
        # Initialize empty data array
        iq0iq1_data = []

        # Arm RX before creating buffers
        self.rx_arm()

        # Check pre rx initialize and if anything is necessary
        # and buffer cleanup

        # Prepare all channels and buffers
        for dev in [self.primary] + self.secondaries:
            dev.rx_destroy_buffer()
            dev._rx_init_channels()

        # sleep(0.1)  # Allow buffers to arm

        # Generate SYNC pulse with sysref_request
        # this will fill up the prepared buffers
        print("Issue SYNC pulse")
        self.sync.sysref_request = 1

        # Gather data from all devices
        print("Save data captured data")
        for dev in [self.primary] + self.secondaries:
            iq0iq1_data += dev.rx()

        # iq0iq1_data = np.array(iq0iq1_data)
        return iq0iq1_data

    def mute_dac_data_sources(self):
        for dev in [self.primary] + self.secondaries:
            for chan in range(4):
                dev._txdac.reg_write(0x80000418 + chan * 0x40, 0x3)

    @property
    def rx_enabled_channels(self) -> Union[List[int], List[str]]:
        if self.primary is None:
            return []
        # Get unions from each device, force them to int and add +2 to each value in second device
        print("===== Gathering enabled channels from primary and secondaries")
        en_channels_dev = [int(v) for v in self.primary.rx_enabled_channels]
        en_channels_dev_secondary = [
            int(v) for v in self.secondaries[0].rx_enabled_channels
        ]
        dev_count = 1
        for dev in self.secondaries:
            en_channels_dev_secondary = [
                int(v) + 2 * dev_count for v in dev.rx_enabled_channels
            ]
            en_channels_dev += en_channels_dev_secondary
            dev_count += 1

        return en_channels_dev

    @rx_enabled_channels.setter
    def rx_enabled_channels(self, value: Union[List[int], List[str]]):
        if self.primary is None:
            return []

        print("SET rx channels  " + str(value))
        temp_secondary_en_channels = []
        temp_primary_en_channels = []
        for i in range(len(self.secondaries)):
            temp_secondary_en_channels.insert(i, [])
        for chn in value:
            if chn in (0, 1):
                temp_primary_en_channels = temp_primary_en_channels + [chn]
            else:
                dev_id = chn // 2
                chn_id = chn % 2
                temp_secondary_en_channels[dev_id - 1] = temp_secondary_en_channels[
                    dev_id - 1
                ] + [chn_id]

        self.primary.rx_enabled_channels = temp_primary_en_channels
        print("SET RX en chnls primary " + str(self.primary.rx_enabled_channels))
        for i in range(len(self.secondaries)):
            self.secondaries[i].rx_enabled_channels = temp_secondary_en_channels[i]
            print("SET RX en chnls sec " + str(self.secondaries[i].rx_enabled_channels))

    @property
    def tx_enabled_channels(self) -> Union[List[int], List[str]]:
        if self.primary is None:
            return []
        # Get unions from each device, force them to int and add +2 to each value in second device
        print("Gathering TX enabled channels from primary and secondaries")
        en_channels_dev = [int(v) for v in self.primary.tx_enabled_channels]
        en_channels_dev_secondary = [
            int(v) for v in self.secondaries[0].tx_enabled_channels
        ]
        dev_count = 1
        for dev in self.secondaries:
            en_channels_dev_secondary = [
                int(v) + 2 * dev_count for v in dev.tx_enabled_channels
            ]
            en_channels_dev += en_channels_dev_secondary
            dev_count += 1

        return en_channels_dev

    @tx_enabled_channels.setter
    def tx_enabled_channels(self, value: Union[List[int], List[str]]):
        if self.primary is None:
            return []

        temp_secondary_en_channels = []
        temp_primary_en_channels = []
        for i in range(len(self.secondaries)):
            temp_secondary_en_channels.insert(i, [])

        for chn in value:
            if chn in (0, 1):
                temp_primary_en_channels = temp_primary_en_channels + [chn]
            else:
                dev_id = chn // 2
                chn_id = chn % 2
                temp_secondary_en_channels[dev_id - 1] = temp_secondary_en_channels[
                    dev_id - 1
                ] + [chn_id]

        self.primary.tx_enabled_channels = temp_primary_en_channels
        print("SET TX en chnls primary " + str(self.primary.tx_enabled_channels))

        for i in range(len(self.secondaries)):
            self.secondaries[i].tx_enabled_channels = temp_secondary_en_channels[i]
            print("SET TX en chnls sec " + str(self.secondaries[i].tx_enabled_channels))

    @property
    def rx_hardwaregain_all_chan0(self):
        """Get RX hardware gain for all channels on primary and secondaries"""
        return self.rx_hardwaregain_chan0

    @rx_hardwaregain_all_chan0.setter
    def rx_hardwaregain_all_chan0(self, value: int):
        """Set TX hardware gain for all channels on primary and secondaries"""
        if self.primary is None:
            return []
        print("Setting TX hardware gain for all channels to " + str(value))
        self.primary.rx_hardwaregain_chan0 = value
        for dev in self.secondaries:
            dev.rx_hardwaregain_chan0 = value

    @property
    def rx_hardwaregain_all_chan1(self):
        """Get RX hardware gain for all channels on primary and secondaries"""
        return self.rx_hardwaregain_chan1

    @rx_hardwaregain_all_chan1.setter
    def rx_hardwaregain_all_chan1(self, value: int):
        """Set TX hardware gain for all channels on primary and secondaries"""
        if self.primary is None:
            return []
        print("Setting RX hardware gain for all channels to " + str(value))
        self.primary.rx_hardwaregain_chan1 = value
        for dev in self.secondaries:
            dev.rx_hardwaregain_chan1 = value

    @property
    def tx_hardwaregain_all_chan0(self):
        """Get TX hardware gain for all channels on primary and secondaries"""
        return self.tx_hardwaregain_chan0

    @tx_hardwaregain_all_chan0.setter
    def tx_hardwaregain_all_chan0(self, value: int):
        """Set TX hardware gain for all channels on primary and secondaries"""
        if self.primary is None:
            return []
        print("Setting TX channel 0 hardware gain for all devices to " + str(value))
        self.primary.tx_hardwaregain_chan0 = value
        for dev in self.secondaries:
            dev.tx_hardwaregain_chan0 = value

    @property
    def tx_hardwaregain_all_chan1(self):
        """Get TX hardware gain for all channels on primary and secondaries"""
        return self.tx_hardwaregain_chan1

    @tx_hardwaregain_all_chan1.setter
    def tx_hardwaregain_all_chan1(self, value: int):
        """Set TX hardware gain for all channels on primary and secondaries"""
        if self.primary is None:
            return []
        print("Setting TX channel 1 hardware gain for all devices to " + str(value))
        self.primary.tx_hardwaregain_chan1 = value
        for dev in self.secondaries:
            dev.tx_hardwaregain_chan1 = value

    #########################################################
    # Application level calibration attributes and methods
    @property
    def gcal(self):
        """pcal: linear gain coefficents for each channel [gain_ch1, gain_ch2, gain_ch3, gain_ch4]"""
        return self.gcal_data

    @gcal.setter
    def gcal(self, values):
        if isinstance(values, list) and all(isinstance(item, float) for item in values):
            if len(values) == (self.num_cal_elements):
                self.gcal_data = values
            else:
                raise ValueError("Input array length doesn't match the expected length")
        else:
            raise TypeError("Input must be a list of floats")

    def save_gain_cal(self, filename="gain_cal_val.pkl"):
        """Saves gain calibration file."""
        with open(filename, "wb") as file:
            pickle.dump(self.gcal, file)
            file.close()

    def load_gain_cal(self, filename="gain_cal_val.pkl"):
        """Load gain calibrated value, if not calibrated set all channel gain correction to 1.
        Parameters
        ----------
        filename: type=stringf
            Provide path of phase calibration file
        """
        try:
            with open(filename, "rb") as file:
                self.gcal = pickle.load(file)  # Load gain cal values
                file.close()
        except FileNotFoundError:
            print("file not found, loading default (no phase shift)")
            self.gcal = [1.1] * (self.num_cal_elements)

    @property
    def pcal(self):
        """pcal: phase differences in degrees [(rx0 - rx1) (rx0 - rx2) (rx0 - rx3)]"""
        return self.pcal_data

    @pcal.setter
    def pcal(self, values):
        if isinstance(values, list) and all(isinstance(item, float) for item in values):
            if len(values) == (self.num_cal_elements - 1):
                self.pcal_data = values
            else:
                raise ValueError("Input array length doesn't match the expected length")
        else:
            raise TypeError("Input must be a list of floats")

    def save_phase_cal(self, filename="phase_cal_val.pkl"):
        """Saves phase calibration file."""
        with open(filename, "wb") as file:
            pickle.dump(self.pcal, file)
            file.close()

    def load_phase_cal(self, filename="phase_cal_val.pkl"):
        """Load phase calibrated value, if not calibrated set all channel phase correction to 0.
        Parameters
        ----------
        filename: type=stringf
            Provide path of phase calibration file
        """
        try:
            with open(filename, "rb") as file:
                self.pcal = pickle.load(file)
                file.close()
        except FileNotFoundError:
            print("file not found, loading default (no phase shift)")
            self.pcal = [0.0] * (self.num_cal_elements - 1)
