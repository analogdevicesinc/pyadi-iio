

class attribute():

    def set_iio_attr_str(self, channel_name, attr_name, output, value):
        channel = self.ctrl.find_channel(channel_name, output)
        try:
            channel.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def set_iio_attr(self, channel_name, attr_name, output, value):
        channel = self.ctrl.find_channel(channel_name, output)
        try:
            channel.attrs[attr_name].value = str(int(value))
        except Exception as ex:
            raise ex

    def get_iio_attr(self, channel_name, attr_name, output):
        channel = self.ctrl.find_channel(channel_name, output)
        return channel.attrs[attr_name].value

    def set_iio_dev_attr_str(self, attr_name, value):
        try:
            self.ctrl.attrs[attr_name].value = str(value)
        except Exception as ex:
            raise ex

    def get_iio_dev_attr(self, attr_name):
        return self.ctrl.attrs[attr_name].value
