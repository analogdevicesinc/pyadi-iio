import pytest
from unittest import mock
from adi import ContextManager as cm
from adi import Pluto
import iio


@mock.patch("iio.scan_contexts", return_value="123456")
@mock.patch("iio.Context", return_value="123456")
def test_context_manager(mocked_Context, mocked_scan_contexts):
    c = cm()
    c.__init_cc__()
    assert not iio.scan_contexts.called
    iio.Context.assert_called_once_with("ip:analog")


@mock.patch("iio.scan_contexts", return_value={"uri1": "FMComms2", "uri2": "PlutoSDR"})
@mock.patch("iio.Context", return_value="123")
def test_context_manager_dev_name_set(mocked_Context, mocked_scan_contexts):
    c = cm()
    dev_name = "PlutoSDR"
    c._device_name = dev_name
    c.__init_cc__()
    iio.scan_contexts.assert_called_once_with()
    iio.Context.assert_called_once_with("uri2")


@mock.patch("iio.scan_contexts")
@mock.patch("iio.Context")
def test_context_manager_uri(mocked_Context, mocked_scan_contexts):
    c = cm()
    uri = "ip:something"
    c.__init_cc__(uri=uri)
    assert not iio.scan_contexts.called
    iio.Context.assert_called_once_with(uri)


@mock.patch("iio.scan_contexts")
@mock.patch("iio.Context")
def test_context_manager_dev_class(mocked_Context, mocked_scan_contexts):
    uri = "ip:something"
    c = Pluto(uri=uri)
    assert not iio.scan_contexts.called
    iio.Context.assert_called_once_with(uri)
    assert iio.Context.return_value.find_device.called
    calls = [
        mock.call("ad9361-phy"),
        mock.call("cf-ad9361-lpc"),
        mock.call().__bool__(),
        mock.call("cf-ad9361-dds-core-lpc"),
        mock.call().__bool__(),
    ]
    iio.Context.return_value.find_device.assert_has_calls(calls)
