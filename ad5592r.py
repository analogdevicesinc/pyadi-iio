import adi

# Set up AD5592R/AD5593R
myad5592r = adi.ad5592r(uri="ip:analog.local")

# Read channels and its parameters
print(myad5592r.channel)
for ch in myad5592r.channel:
    print("Channel Name: ", ch.name)
    print("is Output? ", ch._output)
    print("Channel Raw Value: ", ch.raw)
#    print("Channel Scale: ", ch.scale)
#    print("Channel Offset: ", ch.offset)