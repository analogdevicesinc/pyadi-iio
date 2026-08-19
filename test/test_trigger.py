"""Unit tests for adi.trigger (no hardware / no iio-emu required)."""

from unittest.mock import MagicMock

import iio
import pytest

import adi


def _install_trigger_context(monkeypatch, trigger):
    """Patch context_manager.__init__ to inject a context returning `trigger`."""

    class FakeContext:
        def find_device(self, name):
            return trigger if trigger is not None and name == trigger.name else None

    context = FakeContext()

    def init_context(self, uri="", _device_name=""):
        self._ctx = context
        self.uri = uri

    monkeypatch.setattr("adi.context_manager.context_manager.__init__", init_context)


def _fake_trigger(name, attrs):
    """Build a fake iio.Trigger-like device."""
    trigger = MagicMock(spec=iio.Trigger)
    trigger.name = name
    trigger.attrs = {a: MagicMock() for a in attrs}
    return trigger


def test_hrtimer_trig_reads_and_writes_sampling_frequency(monkeypatch):
    trig = _fake_trigger("trigger0", ["sampling_frequency"])
    trig.attrs["sampling_frequency"].value = "1000"
    _install_trigger_context(monkeypatch, trig)

    dev = adi.trigger.hrtimer_trig()
    assert dev.name == "trigger0"
    assert dev.sampling_frequency == 1000

    dev.sampling_frequency = 2500
    assert trig.attrs["sampling_frequency"].value == "2500"


def test_hrtimer_trig_rejects_missing_device(monkeypatch):
    _install_trigger_context(monkeypatch, None)
    with pytest.raises(Exception, match="not found"):
        adi.trigger.hrtimer_trig(trig_name="missing")


def test_hrtimer_trig_rejects_non_trigger_device(monkeypatch):
    non_trigger = MagicMock()
    non_trigger.name = "not-a-trigger"
    _install_trigger_context(monkeypatch, non_trigger)
    with pytest.raises(ValueError):
        adi.trigger.hrtimer_trig(trig_name="not-a-trigger")


def test_hrtimer_trig_rejects_trigger_without_sampling_frequency(monkeypatch):
    bogus = _fake_trigger("trigger0", ["trigger_now"])
    _install_trigger_context(monkeypatch, bogus)
    with pytest.raises(Exception, match="not a hrtimer trigger"):
        adi.trigger.hrtimer_trig()


def test_sysfs_trig_trigger_now_writes_one(monkeypatch):
    trig = _fake_trigger("sysfstrig0", ["trigger_now"])
    _install_trigger_context(monkeypatch, trig)

    dev = adi.trigger.sysfs_trig()
    assert dev.name == "sysfstrig0"

    dev.trigger_now()
    assert trig.attrs["trigger_now"].value == "1"


def test_sysfs_trig_rejects_missing_device(monkeypatch):
    _install_trigger_context(monkeypatch, None)
    with pytest.raises(Exception, match="not found"):
        adi.trigger.sysfs_trig(trig_name="nope")


def test_sysfs_trig_rejects_missing_trigger_now_attr(monkeypatch):
    trig = _fake_trigger("sysfstrig0", [])
    _install_trigger_context(monkeypatch, trig)
    with pytest.raises(Exception, match="not a sysfs trigger"):
        adi.trigger.sysfs_trig()


def test_sysfs_trig_rejects_wrong_name_prefix(monkeypatch):
    trig = _fake_trigger("trigger0", ["trigger_now"])
    _install_trigger_context(monkeypatch, trig)
    with pytest.raises(Exception, match="not a sysfs trigger"):
        adi.trigger.sysfs_trig(trig_name="trigger0")
