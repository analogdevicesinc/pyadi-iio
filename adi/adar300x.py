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

from adi.attribute import attribute
from adi.context_manager import context_manager


class override:
    def _get_iio_dev_attr_single(self, attr):
        # This is overridden by subclasses
        return [self._get_iio_dev_attr(a) for a in attr]

    def _set_iio_dev_attr_single(self, attr, value):
        # This is overridden by subclasses
        return self._set_iio_dev_attr(attr, value)

    def _get_iio_dev_attr_str_single(self, attr):
        # This is overridden by subclasses
        return [self._get_iio_dev_attr_str(a) for a in attr]

    def _set_iio_dev_attr_str_single(self, attr, value):
        # This is overridden by subclasses
        for a, v in zip(attr, value):
            self._set_iio_dev_attr_str(a, v)


class adar3002(override, attribute, context_manager):
    """ ADAR3002 Ka-Band Beamformer """

    _device_name = ""

    def __init__(self, uri="", driver_name="adar3002", ctx=None):

        self._ctx = ctx
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = self._ctx.find_device(driver_name)
        if not self._ctrl:
            raise Exception(f"{driver_name} not found in context")

        for i in range(4):
            setattr(self, f"beam{i}", self._beam(self._ctrl, f"beam{i}"))

    def _check(self, input, attr, lenl):
        if not isinstance(input, list):
            input = [input]
        assert len(input) <= lenl, f"len({attr}) must be <= {lenl}"
        return input

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

    #########################################

    #########################################

    @property
    def update_intf_ctrl(self):
        """update_intf_ctrl:"""
        names = ["update_intf_ctrl"] * 1
        return self._get_iio_dev_attr_str_single(names)

    @update_intf_ctrl.setter
    def update_intf_ctrl(self, value):
        """update_intf_ctrl:"""
        # assert value in ["pin", "SPI"], "update_intf_ctrl must one of 'pin' 'SPI'"
        self._set_iio_dev_attr_str_single("update_intf_ctrl", value)

    #########################################

    @property
    def amp_bias_mute_ELV(self):
        """amp_bias_mute_EL0V: Select Test Mode."""
        names = [f"amp_bias_mute_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_bias_mute_ELV.setter
    def amp_bias_mute_ELV(self, value):
        value = self._check(value, "amp_bias_mute_ELV", 4)
        names = [f"amp_bias_mute_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################

    @property
    def amp_bias_operational_ELH(self):
        """amp_bias_operational_ELH: Select Test Mode."""
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_bias_operational_ELH.setter
    def amp_bias_operational_ELH(self, value):
        value = self._check(value, "amp_bias_operational_ELH", 4)
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################

    @property
    def amp_bias_operational_ELV(self):
        """amp_bias_operational_ELV: Select Test Mode."""
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_bias_operational_ELV.setter
    def amp_bias_operational_ELV(self, value):
        value = self._check(value, "amp_bias_operational_ELV", 4)
        names = [f"amp_bias_operational_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    # @property
    # def amp_bias_reset_ELH(self):
    #     """amp_bias_reset_ELH: Select Test Mode."""
    #     return [self._get_iio_dev_attr_single(f"amp_bias_reset_EL{v}H") for v in range(4)]

    # @amp_bias_reset_ELH.setter
    # def amp_bias_reset_ELH(self, value):
    #     value = self._check(value, "amp_bias_reset_ELH", 4)
    #     for i, v in enumerate(value):
    #         self._set_iio_dev_attr_str_single(f"amp_bias_reset_EL{i}H", int(v))

    #########################################
    @property
    def amp_bias_reset_ELV(self):
        """amp_bias_reset_ELV: Select Test Mode."""
        names = [f"amp_bias_reset_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_bias_reset_ELV.setter
    def amp_bias_reset_ELV(self, value):
        value = self._check(value, "amp_bias_reset_ELV", 4)
        names = [f"amp_bias_reset_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    @property
    def amp_bias_sleep_ELH(self):
        """amp_bias_sleep_ELH: Select Test Mode."""
        names = [f"amp_bias_sleep_EL{i}H" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_bias_sleep_ELH.setter
    def amp_bias_sleep_ELH(self, value):
        value = self._check(value, "amp_bias_sleep_ELH", 4)
        names = [f"amp_bias_sleep_EL{i}H" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    @property
    def amp_bias_sleep_ELV(self):
        """amp_bias_sleep_ELV: Select Test Mode."""
        names = [f"amp_bias_sleep_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_bias_sleep_ELV.setter
    def amp_bias_sleep_ELV(self, value):
        value = self._check(value, "amp_bias_sleep_ELV", 4)
        names = [f"amp_bias_sleep_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    # @property
    # def amp_en_mute_ELH(self):
    #     """amp_en_mute_ELH: Select Test Mode."""
    #     return [self._get_iio_dev_attr_single(f"amp_en_mute_EL{v}H") for v in range(4)]

    # @amp_en_mute_ELH.setter
    # def amp_en_mute_ELH(self, value):
    #     value = self._check(value, "amp_en_mute_ELH", 4)
    #     for i, v in enumerate(value):
    #         self._set_iio_dev_attr_str_single(f"amp_en_mute_EL{i}H", int(v))

    #########################################
    @property
    def amp_en_mute_ELV(self):
        """amp_en_mute_ELV: Select Test Mode."""
        names = [f"amp_en_mute_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_en_mute_ELV.setter
    def amp_en_mute_ELV(self, value):
        value = self._check(value, "amp_en_mute_ELV", 4)
        names = [f"amp_en_mute_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    @property
    def amp_en_operational_ELH(self):
        """amp_en_operational_ELH: Select Test Mode."""
        names = [f"amp_en_operational_EL{i}H" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_en_operational_ELH.setter
    def amp_en_operational_ELH(self, value):
        value = self._check(value, "amp_en_operational_ELH", 4)
        names = [f"amp_en_operational_EL{i}H" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    @property
    def amp_en_operational_ELV(self):
        """amp_en_operational_ELV: Select Test Mode."""
        names = [f"amp_en_operational_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_en_operational_ELV.setter
    def amp_en_operational_ELV(self, value):
        value = self._check(value, "amp_en_operational_ELV", 4)
        names = [f"amp_en_operational_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    # @property
    # def amp_en_reset_ELH(self):
    #     """amp_en_reset_ELH: Select Test Mode."""
    #     return [self._get_iio_dev_attr_single(f"amp_en_reset_EL{v}H") for v in range(4)]

    # @amp_en_reset_ELH.setter
    # def amp_en_reset_ELH(self, value):
    #     value = self._check(value, "amp_en_reset_ELH", 4)
    #     for i, v in enumerate(value):
    #         self._set_iio_dev_attr_str_single(f"amp_en_reset_EL{i}H", int(v))

    #########################################
    @property
    def amp_en_reset_ELV(self):
        """amp_en_reset_ELV: Select Test Mode."""
        names = [f"amp_en_reset_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_en_reset_ELV.setter
    def amp_en_reset_ELV(self, value):
        value = self._check(value, "amp_en_reset_ELV", 4)
        names = [f"amp_en_reset_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    @property
    def amp_en_sleep_ELH(self):
        """amp_en_sleep_ELH: Select Test Mode."""
        names = [f"amp_en_sleep_EL{i}H" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_en_sleep_ELH.setter
    def amp_en_sleep_ELH(self, value):
        value = self._check(value, "amp_en_sleep_ELH", 4)
        names = [f"amp_en_sleep_EL{i}H" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    #########################################
    @property
    def amp_en_sleep_ELV(self):
        """amp_en_sleep_ELV: Select Test Mode."""
        names = [f"amp_en_sleep_EL{i}V" for i in range(4)]
        return self._get_iio_dev_attr_single(names)

    @amp_en_sleep_ELV.setter
    def amp_en_sleep_ELV(self, value):
        value = self._check(value, "amp_en_sleep_ELV", 4)
        names = [f"amp_en_sleep_EL{i}V" for i in range(4)]
        self._set_iio_dev_attr_str_single(names, value)

    class _beam(attribute):
        """ADAR3002 Beam Control"""

        def __init__(self, ctrl, beam_name):
            self.name = beam_name
            self._ctrl = ctrl

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
            return self._get_iio_dev_attr_str(f"{self.name}_load_mode")

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
            return self._get_iio_dev_attr_str(f"{self.name}_mode")

        @load_mode.setter
        def mode(self, value):
            assert value in [
                "direct",
                "memory",
                "fifo",
                "instant_direct",
                "reset",
                "mute",
            ], "load_mode must be 1 of direct memory fifo instant_direct reset mute"
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


class adar3002_array(adar3002):
    """ ADAR3002 Ka-Band Beamformer Array """

    _device_name = ""

    annotated_properties: bool = False

    def __init__(self, uri="", driver_names=None, ctx=None):

        if driver_names is None:
            driver_names = ["adar3002_T0", "adar3002_T1"]
        self._ctx = ctx
        self._driver_names = driver_names
        context_manager.__init__(self, uri, self._device_name)

        self._chips = [
            adar3002(uri=uri, driver_name=name, ctx=self._ctx)
            for name in self._driver_names
        ]

    def _check(self, input, attr, lenl):
        return input

    # Vector function intercepts
    def _get_iio_dev_attr_single(self, attrs):
        if self.annotated_properties:
            return {
                name: [
                    attribute._get_iio_dev_attr(self, attr, self._ctx.find_device(name))
                    for attr in attrs
                ]
                for name in self._driver_names
            }
        else:
            return [
                attribute._get_iio_dev_attr(self, attr, dev._ctrl)
                for dev in self._chips
                for attr in attrs
            ]

    def _set_iio_dev_attr_str_single(self, attrs, values):
        if isinstance(values, list):
            # Get dimensions
            cs = self.annotated_properties
            self.annotated_properties = True
            vt = self._get_iio_dev_attr_single(attrs)
            self.annotated_properties = cs
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
                self._set_iio_dev_attr(attr, value, self._ctx.find_device(dev))

    def _get_iio_dev_attr_str_single(self, attrs):
        if self.annotated_properties:
            return {
                name: [
                    attribute._get_iio_dev_attr_str(
                        self, attr, self._ctx.find_device(name)
                    )
                    for attr in attrs
                ]
                for name in self._driver_names
            }
        else:
            return [
                attribute._get_iio_dev_attr_str(self, attr, dev._ctrl)
                for dev in self._chips
                for attr in attrs
            ]
