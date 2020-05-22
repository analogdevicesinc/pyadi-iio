import iio
import sysfs
ctx = iio.Context("ip:192.168.86.27")

phydev = None
count = 0
for dev in ctx.devices:
    if "phy" in str(dev.name):
        phydev = dev
        break
    count += 1
if not phydev:
    raise Exception("No PHY devices found")

# # Get sysfs info from device
# sfs = sysfs.sysfs(address = "192.168.86.27",index=count)
# import sys
# sys.exit(0)

# Generate class prototypes
channel_attr_template = """
@property
def {attr_name}(self):
    \"\"\"{attr_name}: <FILL ME IN>\'\"\"\"
    return self._get_iio_attr(\"{channel}\", \"{iio_attr_name}\", {isoutput})

@{attr_name}.setter
def {attr_name}(self, value):
    self._set_iio_attr(\"{channel}\",  \"{iio_attr_name}\", {isoutput}, value)"""

chan = phydev.find_channel("voltage0")

for attr_k in chan.attrs:
    attr = chan.attrs[attr_k]
    print(attr)

    filled = channel_attr_template.format(attr_name = attr.name, channel=chan.id, iio_attr_name = attr.name, isoutput=str(chan.output))
    print(filled)
    # break
