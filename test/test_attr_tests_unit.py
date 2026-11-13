"""Unit tests for the write only helpers in attr_tests (no hardware / no iio-emu required)."""

from test import attr_tests

import pytest


class _WriteOnly:
    """Stand-in for a device or channel with properties that have no getter."""

    written = {}

    def __init__(self, uri="", device_name=""):
        self.channel = {"voltage0": self}

    def _set(name):
        def setter(self, value):
            _WriteOnly.written[name] = value

        return property(None, setter)

    config = _set("config")
    mode = _set("mode")


@pytest.fixture
def fake_dev(monkeypatch):
    # The helpers build the device with eval() in attr_tests' namespace
    monkeypatch.setitem(attr_tests.__dict__, "FakeDev", _WriteOnly)
    _WriteOnly.written = {}
    return _WriteOnly


def test_write_only_str(fake_dev):
    attr_tests.attribute_write_only_str("ip:test", "FakeDev", "config", "abc")
    assert fake_dev.written == {"config": "abc"}


def test_write_only_str_with_depends(fake_dev):
    attr_tests.attribute_write_only_str_with_depends(
        "ip:test", "FakeDev", "config", "abc", {"mode": "fast"}
    )
    assert fake_dev.written == {"mode": "fast", "config": "abc"}


def test_write_only_str_device_channel(fake_dev):
    attr_tests.attribute_write_only_str_device_channel(
        "ip:test", "FakeDev", "fake", "voltage0", "config", "abc"
    )
    assert fake_dev.written == {"config": "abc"}


def test_write_only_str_still_rejects_missing_attr(fake_dev):
    with pytest.raises(AttributeError, match="no attribute named: nope"):
        attr_tests.attribute_write_only_str("ip:test", "FakeDev", "nope", "abc")
