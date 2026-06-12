# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import inspect
from abc import ABCMeta
from typing import Type, TypeVar

from adi.context_manager import context_manager

C = TypeVar("C")


class compatible(context_manager, metaclass=ABCMeta):
    """Abstract Class for Compatible Device

    This class is meant to be inherited by device classes that are compatible
    with multiple IIO devices. It provides a common initialization method that
    checks for compatible devices and connects to the appropriate one based on
    the provided URI and device name. The list of compatible parts can be
    manually defined in the inheriting class or can be automatically populated
    when using compatible.variant() to create derived classes with specific
    compatible matching.
    """

    @staticmethod
    def variant(cls: Type[C], named: str = "", **chip_info) -> Type[C]:
        """Creates a new class that inherits from the given class and is marked
        as compatible with a specific device name. This allows for creating a
        class instance that constraints the search behavior of the constructor
        to a specific compatible device. Example:

        .. code-block:: python

            class adxxxx(attribute, compatible):
                def __init__(self, uri="", device_name=""):
                    compatible.__init__(self, uri, device_name)


            adxx10 = compatible.variant(adxxxx, "adxx10")
            adxx20 = compatible.variant(adxxxx, "adxx20")
            dev_xx = adxxxx(uri)  # searches for all compatible devices in the context
            dev_10 = adxx10(uri)  # searches only for devices compatible with "adxx10"

        :param cls:
            The class to inherit from. This should be a class that inherits from
            compatible.
        :param named:
            The name of the compatible device. This should be one of the names
            listed in the compatible
        :param chip_info:
            Per-part attributes applied to the instance at construction time.
            Stored in the base class _compatible_info dict and set on the object
            after the compatible device is found in the IIO context.
        """
        if not named or not isinstance(named, str):
            raise Exception("Compatible part must be named")

        if not issubclass(cls, compatible):
            raise TypeError(f"{cls.__name__} must inherit from compatible")

        if "compatible_parts" not in cls.__dict__:
            cls.compatible_parts = []
            cls._compatible_info = {}

        if named not in cls.compatible_parts:
            cls.compatible_parts.append(named)
            if chip_info:
                cls._compatible_info[named] = chip_info

        return type(
            named,
            (cls,),
            {
                "_compatible": named,
                "__module__": inspect.stack()[1].frame.f_globals["__name__"],
            },
        )

    def __init__(self, uri="", device_name=""):
        """ Initialize compatible device

        :param uri:
            URI of the IIO context to connect to. If empty, the default context
            will be used.
        :param device_name:
            Name, ID or label of the device to connect to. If empty, the first
            compatible device found will be used.
        """
        if not hasattr(self.__class__, "compatible_parts"):
            raise Exception(
                f"{self.__class__.__name__} is missing the compatible_parts attribute"
            )

        compatible_name = getattr(self.__class__, "_compatible", "")
        if compatible_name:
            if compatible_name not in self.__class__.compatible_parts:
                raise Exception(f"{compatible_name} is not a compatible part")
            compatibles2check = [compatible_name]
        else:
            compatibles2check = self.__class__.compatible_parts
            if len(compatibles2check) == 1:
                compatible_name = compatibles2check[0]

        context_manager.__init__(self, uri, _device_name=compatible_name)

        if not device_name:
            self._ctrl = None

            for device in self._ctx.devices:
                if device.name in compatibles2check:
                    self._ctrl = device
                    break

            # Raise an exception if the device isn't found
            if not self._ctrl:
                raise Exception(f"{self.__class__.__name__} device not found")
        else:
            # allow device_name to be a label or ID
            self._ctrl = self._ctx.find_device(device_name)
            if not self._ctrl:
                raise Exception(f"Device '{device_name}' not found")

            # device name still needs to be a compatible part
            if self._ctrl.name not in compatibles2check:
                raise Exception(f"{self._ctrl.name} is not a compatible part")

        # apply compatible-specific info to the instance
        info = getattr(self.__class__, "_compatible_info", {}).get(self._ctrl.name, {})
        for k, v in info.items():
            setattr(self, k, v)
