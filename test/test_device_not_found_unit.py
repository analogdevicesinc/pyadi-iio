"""Unit tests for missing-device errors (no hardware / no iio-emu required)."""

from unittest.mock import MagicMock

import pytest

import adi


@pytest.mark.parametrize(
    "cls, part", [(adi.ada4961, "ADA4961"), (adi.adf4382, "ADF4382")],
)
def test_missing_device_error_names_the_part(monkeypatch, cls, part):
    # An empty context, so find_device() returns None like libiio does.
    context = MagicMock()
    context.find_device.return_value = None
    monkeypatch.setattr("adi.context_manager.iio.Context", lambda uri: context)

    with pytest.raises(Exception, match=f"^{part} device not found$"):
        cls(uri="ip:test")
