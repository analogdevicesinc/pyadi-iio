import adi

# Set up AD5592r
ad5592r = adi.ad5592r(uri="ip:analog.local")
print(ad5592r.channel)
for ch in ad5592r.channel:
    print(ch.name)
    print(ch._output)
    print(ch.raw)

"""print(ad5592r.channel[0].name)
print(ad5592r.channel[0].raw)
print(ad5592r.channel[0].offset)
print(ad5592r.channel[0].scale)
print((ad5592r.channel[0].raw+ad5592r.channel[0].offset)*ad5592r.channel[0].scale)"""