"""
Unit tests for refactored device classes using device_base pattern.
These tests verify the refactoring maintains correct structure and interfaces.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

import adi


class TestPatternARXDevices:
    """Test Pattern A RX devices (with channel objects)"""

    @pytest.mark.parametrize(
        "device_class,expected_parts",
        [
            (adi.ad7124, ["ad7124-8", "ad7124-4"]),
            (adi.ad7134, ["ad7134", "ad4134"]),
            (adi.ad4020, ["ad4020", "ad4021", "ad4022"]),
            (adi.ad4080, ["ad4080"]),
            (adi.ad4110, ["ad4110"]),
            (adi.ad4130, ["ad4130-8"]),
            (adi.ad4170, ["ad4170", "ad4190"]),
            (
                adi.ad717x,
                [
                    "ad4111",
                    "ad4112",
                    "ad4113",
                    "ad4114",
                    "ad4115",
                    "ad4116",
                    "ad7172-2",
                    "ad7172-4",
                    "ad7173-8",
                    "ad7175-2",
                    "ad7175-8",
                    "ad7176-2",
                    "ad7177-2",
                ],
            ),
            (adi.ad719x, ["ad7190", "ad7191", "ad7192", "ad7193", "ad7194", "ad7195"]),
            (
                adi.ad738x,
                [
                    "ad7380",
                    "ad7380-4",
                    "ad7389-4",
                    "ad7381",
                    "ad7381-4",
                    "ad7383",
                    "ad7384",
                    "ad7386",
                    "ad7387",
                    "ad7388",
                    "ad4680",
                    "ad4681",
                    "ad4682",
                    "ad4683",
                ],
            ),
            (adi.ad777x, ["ad7770", "ad7771", "ad7779"]),
        ],
    )
    def test_compatible_parts_attribute(self, device_class, expected_parts):
        """Verify all refactored devices have compatible_parts class attribute"""
        assert hasattr(
            device_class, "compatible_parts"
        ), f"{device_class.__name__} missing compatible_parts"
        assert (
            device_class.compatible_parts == expected_parts
        ), f"{device_class.__name__} has incorrect compatible_parts"

    @pytest.mark.parametrize(
        "device_class,channel_class_name",
        [
            (adi.ad7124, "ad7124_channel"),
            (adi.ad7134, "ad7134_channel"),
            (adi.ad4020, "ad4020_channel"),
            (adi.ad4080, "ad4080_channel"),
            (adi.ad4110, "ad4110_channel"),
            (adi.ad4130, "ad4130_channel"),
            (adi.ad4170, "ad4170_channel"),
            (adi.ad717x, "ad717x_channel"),
            (adi.ad719x, "ad719x_channel"),
            (adi.ad738x, "ad738x_channel"),
            (adi.ad777x, "ad777x_channel"),
        ],
    )
    def test_channel_def_attribute(self, device_class, channel_class_name):
        """Verify all Pattern A devices have _channel_def attribute"""
        assert hasattr(
            device_class, "_channel_def"
        ), f"{device_class.__name__} missing _channel_def"
        channel_class = device_class._channel_def
        assert (
            channel_class.__name__ == channel_class_name
        ), f"{device_class.__name__} has wrong channel class"

    @pytest.mark.parametrize(
        "device_class",
        [
            adi.ad7124,
            adi.ad7134,
            adi.ad4020,
            adi.ad4080,
            adi.ad4110,
            adi.ad4130,
            adi.ad4170,
            adi.ad717x,
            adi.ad719x,
            adi.ad738x,
            adi.ad777x,
        ],
    )
    def test_complex_data_attribute(self, device_class):
        """Verify _complex_data attribute exists and is False"""
        assert hasattr(
            device_class, "_complex_data"
        ), f"{device_class.__name__} missing _complex_data"
        assert (
            device_class._complex_data == False
        ), f"{device_class.__name__} should have _complex_data=False"

    @pytest.mark.parametrize(
        "device_class",
        [
            adi.ad7124,
            adi.ad7134,
            adi.ad4020,
            adi.ad4080,
            adi.ad4110,
            adi.ad4130,
            adi.ad4170,
            adi.ad717x,
            adi.ad719x,
            adi.ad738x,
            adi.ad777x,
        ],
    )
    def test_channel_list_attribute(self, device_class):
        """Verify channel list attribute exists"""
        assert hasattr(
            device_class, "channel"
        ), f"{device_class.__name__} missing channel attribute"


class TestPatternATXDevices:
    """Test Pattern A TX devices (with channel objects)"""

    @pytest.mark.parametrize(
        "device_class,expected_parts",
        [
            (adi.ad579x, ["ad5780", "ad5781", "ad5790", "ad5791", "ad5760"]),
            (adi.ad5754r, ["ad5754r"]),
        ],
    )
    def test_compatible_parts_attribute(self, device_class, expected_parts):
        """Verify TX devices have compatible_parts"""
        assert hasattr(device_class, "compatible_parts")
        assert device_class.compatible_parts == expected_parts

    @pytest.mark.parametrize(
        "device_class,channel_class_name",
        [(adi.ad579x, "ad579x_channel"), (adi.ad5754r, "ad5754r_channel"),],
    )
    def test_channel_def_attribute(self, device_class, channel_class_name):
        """Verify TX devices have _channel_def attribute"""
        assert hasattr(device_class, "_channel_def")
        channel_class = device_class._channel_def
        assert channel_class.__name__ == channel_class_name


class TestPatternBDevices:
    """Test Pattern B devices (without channel objects)"""

    @pytest.mark.parametrize(
        "device_class,expected_parts", [(adi.ad2s1210, ["ad2s1210"]),]
    )
    def test_compatible_parts_attribute(self, device_class, expected_parts):
        """Verify Pattern B devices have compatible_parts"""
        assert hasattr(device_class, "compatible_parts")
        assert device_class.compatible_parts == expected_parts


class TestChannelClasses:
    """Test channel class interfaces"""

    @pytest.mark.parametrize(
        "module_name,channel_class_name,expected_attrs",
        [
            ("ad7124", "ad7124_channel", ["raw", "scale", "offset"]),
            ("ad7134", "ad7134_channel", ["raw", "scale"]),
            ("ad4020", "ad4020_channel", ["raw", "scale"]),
            ("ad4080", "ad4080_channel", ["scale"]),  # ad4080 only has scale
            ("ad4110", "ad4110_channel", ["raw", "scale", "offset"]),
            ("ad4130", "ad4130_channel", ["raw", "scale", "offset"]),
            ("ad4170", "ad4170_channel", ["raw", "scale", "offset"]),
            ("ad717x", "ad717x_channel", ["raw", "scale"]),
            ("ad719x", "ad719x_channel", ["raw", "scale", "offset"]),
            ("ad738x", "ad738x_channel", ["raw", "scale", "offset"]),
            ("ad777x", "ad777x_channel", ["raw", "scale", "offset"]),
            ("ad579x", "ad579x_channel", ["raw", "scale", "offset", "powerdown"]),
            (
                "ad5754r",
                "ad5754r_channel",
                ["raw", "scale", "offset", "powerup", "range"],
            ),
        ],
    )
    def test_channel_class_properties(
        self, module_name, channel_class_name, expected_attrs
    ):
        """Verify channel classes have expected properties"""
        module = __import__(f"adi.{module_name}", fromlist=[channel_class_name])
        channel_class = getattr(module, channel_class_name)

        for attr in expected_attrs:
            assert hasattr(
                channel_class, attr
            ), f"{channel_class_name} missing {attr} property"
            # Check if it's a property
            class_attr = getattr(channel_class, attr)
            assert isinstance(
                class_attr, property
            ), f"{channel_class_name}.{attr} should be a property"


class TestDeviceSpecificFeatures:
    """Test device-specific features preserved after refactoring"""

    def test_ad7124_has_post_init(self):
        """Verify ad7124 has __post_init__ for channel sorting"""
        assert hasattr(adi.ad7124, "__post_init__")

    def test_ad579x_has_post_init(self):
        """Verify ad579x has __post_init__ for output_bits"""
        assert hasattr(adi.ad579x, "__post_init__")

    def test_ad5754r_has_post_init(self):
        """Verify ad5754r has __post_init__ for output_bits"""
        assert hasattr(adi.ad5754r, "__post_init__")

    def test_ad2s1210_has_post_init(self):
        """Verify ad2s1210 has __post_init__ for custom channels"""
        assert hasattr(adi.ad2s1210, "__post_init__")

    def test_ad2s1210_custom_channels(self):
        """Verify ad2s1210 has custom channel classes"""
        # Import the module to get the classes defined in the file
        import importlib
        import sys

        mod = importlib.import_module("adi.ad2s1210")
        # The classes are defined in the module but not exported at module level
        # Check that they're used in the code by verifying the class has the attribute
        assert hasattr(mod.ad2s1210_position_channel, "raw")
        assert hasattr(mod.ad2s1210_velocity_channel, "raw")

    def test_ad579x_device_level_properties(self):
        """Verify ad579x has device-level properties"""
        assert hasattr(adi.ad579x, "powerdown_mode")
        assert hasattr(adi.ad579x, "sampling_frequency")

    def test_ad5754r_device_level_properties(self):
        """Verify ad5754r has many device-level properties"""
        device_properties = [
            "int_ref_powerup",
            "clear_setting",
            "sdo_disable",
            "sampling_frequency",
            "clamp_enable",
            "tsd_enable",
            "oc_tsd",
            "all_chns_clear",
            "sw_ldac_trigger",
            "hw_ldac_trigger",
        ]
        for prop in device_properties:
            assert hasattr(adi.ad5754r, prop), f"ad5754r missing {prop} property"


class TestToVoltsConversion:
    """Test to_volts methods preserved in refactored devices"""

    @pytest.mark.parametrize(
        "device_class",
        [
            adi.ad7134,
            adi.ad717x,
            adi.ad719x,
            adi.ad738x,
            adi.ad777x,
            adi.ad4170,
            adi.ad4130,
        ],
    )
    def test_to_volts_method_exists(self, device_class):
        """Verify devices with to_volts method still have it"""
        assert hasattr(
            device_class, "to_volts"
        ), f"{device_class.__name__} missing to_volts method"
        import inspect

        assert callable(
            device_class.to_volts
        ), f"{device_class.__name__}.to_volts should be callable"


class TestInheritanceStructure:
    """Test that refactored devices use correct base classes"""

    @pytest.mark.parametrize(
        "device_class,expected_base_name",
        [
            (adi.ad7124, "rx_chan_comp"),
            (adi.ad7134, "rx_chan_comp"),
            (adi.ad4020, "rx_chan_comp"),
            (adi.ad4080, "rx_chan_comp"),
            (adi.ad4110, "rx_chan_comp"),
            (adi.ad4130, "rx_chan_comp"),
            (adi.ad4170, "rx_chan_comp"),
            (adi.ad717x, "rx_chan_comp"),
            (adi.ad719x, "rx_chan_comp"),
            (adi.ad738x, "rx_chan_comp"),
            (adi.ad777x, "rx_chan_comp"),
            (adi.ad579x, "tx_chan_comp"),
            (adi.ad5754r, "tx_chan_comp_no_buff"),
            (adi.ad2s1210, "rx_def"),
        ],
    )
    def test_inheritance_from_device_base(self, device_class, expected_base_name):
        """Verify devices inherit from correct device_base classes"""
        # Get base class names
        bases = [base.__name__ for base in device_class.__bases__]
        assert (
            expected_base_name in bases
        ), f"{device_class.__name__} should inherit from {expected_base_name}, has: {bases}"


class TestBackwardsCompatibility:
    """Test that refactored devices maintain backwards compatibility"""

    @pytest.mark.parametrize(
        "device_class",
        [
            adi.ad7124,
            adi.ad7134,
            adi.ad4020,
            adi.ad4080,
            adi.ad4110,
            adi.ad4130,
            adi.ad4170,
            adi.ad717x,
            adi.ad719x,
            adi.ad738x,
            adi.ad777x,
            adi.ad579x,
            adi.ad5754r,
            adi.ad2s1210,
        ],
    )
    def test_device_name_attribute(self, device_class):
        """Verify _device_name attribute still exists for compatibility"""
        assert hasattr(
            device_class, "_device_name"
        ), f"{device_class.__name__} missing _device_name attribute"

    @pytest.mark.parametrize(
        "device_class",
        [
            adi.ad7124,
            adi.ad7134,
            adi.ad4020,
            adi.ad4080,
            adi.ad4110,
            adi.ad4130,
            adi.ad4170,
            adi.ad717x,
            adi.ad719x,
            adi.ad738x,
            adi.ad777x,
        ],
    )
    def test_rx_channel_list_exists(self, device_class):
        """Verify RX devices have channel attribute"""
        # Channel attribute should be class variable
        assert "channel" in dir(
            device_class
        ), f"{device_class.__name__} should have channel attribute"


class TestDeviceFamilies:
    """Test device family support (ad4020 family with subclasses)"""

    def test_ad4020_family_classes_exist(self):
        """Verify ad4020 family has all subclass variants"""
        # Import all the family classes from adi
        from adi import ad4000, ad4001, ad4002, ad4003, ad4020

        # Check main class
        assert ad4020 is not None
        assert ad4020.compatible_parts == ["ad4020", "ad4021", "ad4022"]

        # Check subclasses exist and have compatible_parts
        assert ad4000 is not None
        assert ad4000.compatible_parts is not None
        assert ad4001 is not None
        assert ad4001.compatible_parts is not None
        assert ad4002 is not None
        assert ad4002.compatible_parts is not None
        assert ad4003 is not None
        assert ad4003.compatible_parts is not None


class TestDocumentation:
    """Test that classes have proper documentation"""

    @pytest.mark.parametrize(
        "device_class",
        [
            adi.ad7124,
            adi.ad7134,
            adi.ad4020,
            adi.ad4080,
            adi.ad4110,
            adi.ad4130,
            adi.ad4170,
            adi.ad717x,
            adi.ad719x,
            adi.ad738x,
            adi.ad777x,
            adi.ad579x,
            adi.ad5754r,
            adi.ad2s1210,
        ],
    )
    def test_class_has_docstring(self, device_class):
        """Verify all refactored device classes have docstrings"""
        assert (
            device_class.__doc__ is not None
        ), f"{device_class.__name__} missing docstring"
        assert (
            len(device_class.__doc__.strip()) > 0
        ), f"{device_class.__name__} has empty docstring"
