"""Multi-chip synchronization for ADRV9002 transceivers across FPGAs"""
import logging

from .adrv9002 import adrv9002
from .context_manager import context_manager
from .attribute import attribute
from .sshfs import sshfs

logger = logging.getLogger(__name__)

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
            dev._get_iio_dev_attr(attr, _get_ctrl(_ctrl, dev))
            for dev in self._devices
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

class adrv9002_multi(map_to_multi_devices, adrv9002):

    primary = None
    secondaries = []

    def __init__(
        self,
        primary_uri="ip:analog.local",
        secondary_uris=[],
        sync_uri="ip:synchrona.local",
        enable_ssh=False,
        sshargs=None,
    ):

        # Mirror top level design off single device
        adrv9002.__init__(self, uri=primary_uri)

        # Reuse context for primary
        class adrv9002_primary(adrv9002):
            def __init__(self, ctx, uri) -> None:
                self._ctx = ctx
                self.uri = uri
                super().__init__(uri)
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

    def __del__(self):
        # self.primary.__del__()
        for secondary in self.secondaries:
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

