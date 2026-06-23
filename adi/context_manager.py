# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import iio


class context_manager(object):
    _uri_auto = "ip:analog"
    _ctx = None

    @property
    def ctx(self) -> iio.Context:
        """IIO Context"""
        return self._ctx

    def __init__(self, uri="", _device_name=""):
        if self._ctx:
            return
        self.uri = uri
        try:
            if self.uri == "":
                # Try USB contexts first
                if _device_name != "":
                    contexts = iio.scan_contexts()
                    for c in contexts:
                        if _device_name in contexts[c]:
                            self._ctx = iio.Context(c)
                            break
                # Try auto discover
                if not self._ctx and self._uri_auto != "":
                    self._ctx = iio.Context(self._uri_auto)
                if not self._ctx:
                    raise Exception("No device found")
            else:
                self._ctx = iio.Context(self.uri)
        except BaseException:
            raise Exception("No device found")

    def close(self):
        """Close the IIO context"""
        if self._ctx:
            del self._ctx
            self._ctx = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
