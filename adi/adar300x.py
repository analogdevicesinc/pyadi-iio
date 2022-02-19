# Copyright (C) 2022 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re

from adi.attribute import attribute
from adi.context_manager import context_manager


class override:
    def _tolist(self, d: dict):
        if not self._annotated_properties:
            nout = []
            for value in d.values():
                nout += value
            d = nout
        return d

    def _get_iio_dev_attr_vec(self, attrs):
        return self._tolist(
            {
                dev.name: [self._get_iio_dev_attr(attr, dev) for attr in attrs]
                for dev in self._ctrls
            }
        )

    def _set_iio_dev_attr_vec(self, attrs, values):
        # Convert values to dict if not already
        if isinstance(values, list):
            # Get dimensions
            cs = self._annotated_properties
            self._annotated_properties = True
            vt = self._get_iio_dev_attr_vec(attrs)
            self._annotated_properties = cs
            num_props = sum(len(vt[key]) for key in vt)
            if num_props != len(values):
                raise Exception(
                    f"Input to invalid size. {num_props} expected, got {len(values)}"
                )
            dvalues = {}
            used = 0
            # Create dict from list
            for key in vt:
                needed = len(vt[key])
                dvalues[key] = values[used : used + needed]
                used += needed
        else:
            dvalues = values
        for dev in dvalues:
            for attr, value in zip(attrs, dvalues[dev]):
                attribute._set_iio_dev_attr(
                    self, attr, value, self._ctx.find_device(dev),
                )


class adar300x(override, attribute, context_manager):
    """ADAR3002 Ka-Band Beamformer"""

    _device_name = ""
    _annotated_properties = False

    def _get_labeled_channels(self, regx, sort_by_label=True):
        channels = {}
        for ctrl in self._ctrls:
            ids = []
            labels = []
            for chan in ctrl.channels:
                if "label" in chan.attrs and re.match(
                    regx, str(chan.attrs["label"].value)
                ):
                    ids.append(chan.id)
                    labels.append(chan.attrs["label"].value)

            if sort_by_label:
                channels[ctrl.name] = [x for _, x in sorted(zip(labels, ids))]

        return channels

    def __init__(
        self, uri="", driver_names=["adar3002_csb_0_0", "adar3002_csb_0_2"], ctx=None
    ):

        if not isinstance(driver_names, list):
            driver_names = [driver_names]

        self._ctx = ctx
        context_manager.__init__(self, uri, self._device_name)

        self._ctrls = []
        for driver_name in driver_names:
            ctrl = self._ctx.find_device(driver_name)
            if not ctrl:
                raise Exception(f"{driver_name} not found in context")
            self._ctrls.append(ctrl)

        for i in range(4):
            setattr(self, f"beam{i}", self._beam(self._ctrls, f"beam{i}", self._ctx))

        # Collect channels of interest
        self._vphase_channel_names = self._get_labeled_channels("BEAM\d_V_EL\d_DELAY")
        self._hphase_channel_names = self._get_labeled_channels("BEAM\d_H_EL\d_DELAY")
        self._vpower_channel_names = self._get_labeled_channels(
            "BEAM\d_V_EL\d_ATTENUATION"
        )
        self._hpower_channel_names = self._get_labeled_channels(
            "BEAM\d_H_EL\d_ATTENUATION"
        )

    def __repr__(self):
        str = ""
        for var in dir(self):
            if var and var[0] != "_":
                v = getattr(self, var)
                if isinstance(v, adar3002._beam):
                    for varb in dir(v):
                        if varb and varb[0] != "_":
                            vb = getattr(v, varb)
                            str += f"{var}.{varb}: {vb}\n"
                else:
                    str += f"{var}: {getattr(self,var)}\n"
        return str

    def _get_iio_attr_vec(self, channels, attr, out):
        out = {
            dev.name: attribute._get_iio_attr_vec(
                self, channels[dev.name], attr, True, dev
            )
            for dev in self._ctrls
        }
        return self._tolist(out)

    def _set_iio_attr_int_vec(self, channels, attr_name, output, values):
        # Convert values to dict if not already
        if isinstance(values, list):
            # Get dimensions
            cs = self._annotated_properties
            self._annotated_properties = True
            vt = self._get_iio_attr_vec(channels, attr_name, output)
            self._annotated_properties = cs
            num_props = sum(len(vt[key]) for key in vt)
            if num_props != len(values):
                raise Exception(
                    f"Input to invalid size. {num_props} expected, got {len(values)}"
                )
            dvalues = {}
            used = 0
            # Create dict from list
            for key in vt:
                needed = len(vt[key])
                dvalues[key] = values[used : used + needed]
                used += needed
        else:
            dvalues = values
        for dev in dvalues:
            attribute._set_iio_attr_int_vec(
                self,
                channels[dev],
                attr_name,
                output,
                dvalues[dev],
                self._ctx.find_device(dev),
            )

    #########################################
    @property
    def phases_V(self):
        """phases_V: Select Test Mode."""
        return self._get_iio_attr_vec(self._vphase_channel_names, "raw", True)

    @phases_V.setter
    def phases_V(self, value):
        self._set_iio_attr_int_vec(self._vphase_channel_names, "raw", True, value)

    @property
    def phases_H(self):
        """phases_H: Select Test Mode."""
        return self._get_iio_attr_vec(self._hphase_channel_names, "raw", True)

    @phases_H.setter
    def phases_H(self, value):
        self._set_iio_attr_int_vec(self._hphase_channel_names, "raw", True, value)

    @property
    def powers_V(self):
        """powers_V: Select Test Mode."""
        return self._get_iio_attr_vec(self._vpower_channel_names, "raw", True)

    @powers_V.setter
    def powers_V(self, value):
        self._set_iio_attr_int_vec(self._vpower_channel_names, "raw", True, value)

    @property
    def powers_H(self):
        """powers_H: Select Test Mode."""
        return self._get_iio_attr_vec(self._hpower_channel_names, "raw", True)

    @powers_H.setter
    def powers_H(self, value):
        self._set_iio_attr_int_vec(self._hpower_channel_names, "raw", True, value)

    #########################################

    # @property
    # def update_intf_ctrl(self):
    #     """update_intf_ctrl:"""
    #     names = ["update_intf_ctrl"] * 1
    #     return self._get_iio_dev_attr_str_single(names)

    # @update_intf_ctrl.setter
    # def update_intf_ctrl(self, value):
    #     """update_intf_ctrl:"""
    #     # assert value in ["pin", "SPI"], "update_intf_ctrl must one of 'pin' 'SPI'"
    #     self._set_iio_dev_attr_vec("update_intf_ctrl", value)

    #########################################

    @property
    def amp_bias_mute_ELV(self):
        """amp_bias_mute_EL0V: Select Test Mode."""
        names = [f"amp_bias_mute_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_bias_mute_ELV.setter
    def amp_bias_mute_ELV(self, value):
        # value = self._check(value, "amp_bias_mute_ELV", 4)
        names = [f"amp_bias_mute_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################

    @property
    def amp_bias_operational_ELH(self):
        """amp_bias_operational_ELH: Select Test Mode."""
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_bias_operational_ELH.setter
    def amp_bias_operational_ELH(self, value):
        value = self._check(value, "amp_bias_operational_ELH", 4)
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################

    @property
    def amp_bias_operational_ELV(self):
        """amp_bias_operational_ELV: Select Test Mode."""
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_bias_operational_ELV.setter
    def amp_bias_operational_ELV(self, value):
        value = self._check(value, "amp_bias_operational_ELV", 4)
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    # @property
    # def amp_bias_reset_ELH(self):
    #     """amp_bias_reset_ELH: Select Test Mode."""
    #     return [self._get_iio_dev_attr_vec(f"amp_bias_reset_EL{v}H") for v in range(4)]

    # @amp_bias_reset_ELH.setter
    # def amp_bias_reset_ELH(self, value):
    #     value = self._check(value, "amp_bias_reset_ELH", 4)
    #     for i, v in enumerate(value):
    #         self._set_iio_dev_attr_vec(f"amp_bias_reset_EL{i}H", int(v))

    #########################################
    @property
    def amp_bias_reset_ELV(self):
        """amp_bias_reset_ELV: Select Test Mode."""
        names = [f"amp_bias_reset_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_bias_reset_ELV.setter
    def amp_bias_reset_ELV(self, value):
        value = self._check(value, "amp_bias_reset_ELV", 4)
        names = [f"amp_bias_reset_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    @property
    def amp_bias_sleep_ELH(self):
        """amp_bias_sleep_ELH: Select Test Mode."""
        names = [f"amp_bias_sleep_EL{i}H" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_bias_sleep_ELH.setter
    def amp_bias_sleep_ELH(self, value):
        value = self._check(value, "amp_bias_sleep_ELH", 4)
        names = [f"amp_bias_sleep_EL{i}H" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    @property
    def amp_bias_sleep_ELV(self):
        """amp_bias_sleep_ELV: Select Test Mode."""
        names = [f"amp_bias_sleep_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_bias_sleep_ELV.setter
    def amp_bias_sleep_ELV(self, value):
        value = self._check(value, "amp_bias_sleep_ELV", 4)
        names = [f"amp_bias_sleep_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    # @property
    # def amp_en_mute_ELH(self):
    #     """amp_en_mute_ELH: Select Test Mode."""
    #     return [self._get_iio_dev_attr_vec(f"amp_en_mute_EL{v}H") for v in range(4)]

    # @amp_en_mute_ELH.setter
    # def amp_en_mute_ELH(self, value):
    #     value = self._check(value, "amp_en_mute_ELH", 4)
    #     for i, v in enumerate(value):
    #         self._set_iio_dev_attr_vec(f"amp_en_mute_EL{i}H", int(v))

    #########################################
    @property
    def amp_en_mute_ELV(self):
        """amp_en_mute_ELV: Select Test Mode."""
        names = [f"amp_en_mute_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_en_mute_ELV.setter
    def amp_en_mute_ELV(self, value):
        value = self._check(value, "amp_en_mute_ELV", 4)
        names = [f"amp_en_mute_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    @property
    def amp_en_operational_ELH(self):
        """amp_en_operational_ELH: Select Test Mode."""
        names = [f"amp_en_operational_EL{i}H" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_en_operational_ELH.setter
    def amp_en_operational_ELH(self, value):
        value = self._check(value, "amp_en_operational_ELH", 4)
        names = [f"amp_en_operational_EL{i}H" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    @property
    def amp_en_operational_ELV(self):
        """amp_en_operational_ELV: Select Test Mode."""
        names = [f"amp_en_operational_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_en_operational_ELV.setter
    def amp_en_operational_ELV(self, value):
        value = self._check(value, "amp_en_operational_ELV", 4)
        names = [f"amp_en_operational_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    # @property
    # def amp_en_reset_ELH(self):
    #     """amp_en_reset_ELH: Select Test Mode."""
    #     return [self._get_iio_dev_attr_vec(f"amp_en_reset_EL{v}H") for v in range(4)]

    # @amp_en_reset_ELH.setter
    # def amp_en_reset_ELH(self, value):
    #     value = self._check(value, "amp_en_reset_ELH", 4)
    #     for i, v in enumerate(value):
    #         self._set_iio_dev_attr_vec(f"amp_en_reset_EL{i}H", int(v))

    #########################################
    @property
    def amp_en_reset_ELV(self):
        """amp_en_reset_ELV: Select Test Mode."""
        names = [f"amp_en_reset_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_en_reset_ELV.setter
    def amp_en_reset_ELV(self, value):
        value = self._check(value, "amp_en_reset_ELV", 4)
        names = [f"amp_en_reset_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    @property
    def amp_en_sleep_ELH(self):
        """amp_en_sleep_ELH: Select Test Mode."""
        names = [f"amp_en_sleep_EL{i}H" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_en_sleep_ELH.setter
    def amp_en_sleep_ELH(self, value):
        value = self._check(value, "amp_en_sleep_ELH", 4)
        names = [f"amp_en_sleep_EL{i}H" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    #########################################
    @property
    def amp_en_sleep_ELV(self):
        """amp_en_sleep_ELV: Select Test Mode."""
        names = [f"amp_en_sleep_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_vec(names)

    @amp_en_sleep_ELV.setter
    def amp_en_sleep_ELV(self, value):
        value = self._check(value, "amp_en_sleep_ELV", 4)
        names = [f"amp_en_sleep_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_vec(names, value)

    class _beam(override, attribute):
        """ADAR3002 Beam Control"""

        _annotated_properties = False

        def __init__(self, ctrls, beam_name, ctx):
            self.name = beam_name
            self._ctrls = ctrls
            self._ctx = ctx

        def _get_iio_dev_attr(self, attr):
            return self._tolist(
                {
                    dev.name: [attribute._get_iio_dev_attr(self, attr, dev)]
                    for dev in self._ctrls
                }
            )

        def _get_iio_dev_attr_strb(self, attr):
            return self._tolist(
                {
                    dev.name: [attribute._get_iio_dev_attr_str(self, attr, dev)]
                    for dev in self._ctrls
                }
            )

        def _prep(self, attr, values):
            # Convert values to dict if not already
            if isinstance(values, list):
                # Get dimensions
                cs = self._annotated_properties
                self._annotated_properties = True
                vt = self._get_iio_dev_attr(attr)
                self._annotated_properties = cs
                num_props = sum(len(vt[key]) for key in vt)
                if num_props != len(values):
                    raise Exception(
                        f"Input to invalid size. {num_props} expected, got {len(values)}"
                    )
                dvalues = {}
                used = 0
                # Create dict from list
                for key in vt:
                    needed = len(vt[key])
                    dvalues[key] = values[used : used + needed]
                    used += needed
            else:
                dvalues = values
            return dvalues

        def _set_iio_dev_attr(self, attr, dvalues):
            dvalues = self._prep(attr, dvalues)
            for dev in dvalues:
                for value in dvalues[dev]:
                    attribute._set_iio_dev_attr(
                        self, attr, value, self._ctx.find_device(dev),
                    )

        def _set_iio_dev_attr_str(self, attr, dvalues):
            dvalues = self._prep(attr, dvalues)
            for dev in dvalues:
                for value in dvalues[dev]:
                    attribute._set_iio_dev_attr_str(
                        self, attr, value, self._ctx.find_device(dev),
                    )

        @property
        def fifo_rd(self):
            """fifo_rd:"""
            return self._get_iio_dev_attr(f"{self.name}_fifo_rd")

        @fifo_rd.setter
        def fifo_rd(self, value):
            self._set_iio_dev_attr(f"{self.name}_fifo_rd", value)

        @property
        def fifo_wr(self):
            """fifo_wr:"""
            return self._get_iio_dev_attr(f"{self.name}_fifo_wr")

        @fifo_wr.setter
        def fifo_wr(self, value):
            self._set_iio_dev_attr(f"{self.name}_fifo_wr", value)

        @property
        def load_mode(self):
            """load_mode:"""
            return self._get_iio_dev_attr_strb(f"{self.name}_load_mode")

        @load_mode.setter
        def load_mode(self, value):
            assert value in [
                "direct",
                "memory",
                "fifo",
                "instant_direct",
                "reset",
                "mute",
            ], "load_mode must be 1 of direct memory fifo instant_direct reset mute"
            self._set_iio_dev_attr_str(f"{self.name}_load_mode", value)

        @property
        def mode(self):
            """mode:"""
            return self._get_iio_dev_attr_strb(f"{self.name}_mode")

        @mode.setter
        def mode(self, value):
            assert value in [
                "direct",
                "memory",
                "fifo",
                "instant_direct",
                "reset",
                "mute",
            ], "mode must be 1 of direct memory fifo instant_direct reset mute"
            self._set_iio_dev_attr_str_single(f"{self.name}_mode", value)

        @property
        def ram_index(self):
            """ram_index:"""
            return self._get_iio_dev_attr(f"{self.name}_ram_index")

        @ram_index.setter
        def ram_index(self, value):
            self._set_iio_dev_attr(f"{self.name}_ram_index", value)

        @property
        def ram_start(self):
            """ram_start:"""
            return self._get_iio_dev_attr(f"{self.name}_ram_start")

        @ram_start.setter
        def ram_start(self, value):
            self._set_iio_dev_attr(f"{self.name}_ram_start", value)

        @property
        def ram_stop(self):
            """ram_stop:"""
            return self._get_iio_dev_attr(f"{self.name}_ram_stop")

        @ram_stop.setter
        def ram_stop(self, value):
            self._set_iio_dev_attr(f"{self.name}_ram_stop", value)

        @property
        def update(self):
            """update:"""
            return self._get_iio_dev_attr(f"{self.name}_update")

        @update.setter
        def update(self, value):
            self._set_iio_dev_attr(self.name, f"{self.name}_update", value)


class adar3002(adar300x):
    def __init__(self, uri="", driver_name="adar3002_csb_0_0", ctx=None):
        if not isinstance(driver_name, str):
            raise Exception("driver_name must be string")
        super().__init__(uri, [driver_name], ctx)


class adar3002_array(adar300x):
    @property
    def annotated_properties(self):
        """annotated_properties:"""
        return self._annotated_properties

    @annotated_properties.setter
    def annotated_properties(self, value):
        self._annotated_properties = value
