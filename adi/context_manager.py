from __future__ import print_function
import sys
import iio


class context_manager(object):
    uri_auto = 'ip:analog'
    ctx = None

    def __init__(self, uri="", device_name=""):
        self.uri = uri
        try:
            if self.uri == '':
                # Try USB contexts first
                if device_name != '':
                    contexts = iio.scan_contexts()
                    for c in contexts:
                        if device_name in contexts[c]:
                            self.ctx = iio.Context(c)
                            break
                # Try auto discover
                if not self.ctx and self.uri_auto != '':
                    self.ctx = iio.Context(self.uri_auto)
                if not self.ctx:
                    raise
            else:
                self.ctx = iio.Context(self.uri)
        except BaseException:
            raise Exception("No device found")
