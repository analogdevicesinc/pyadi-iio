import adi

ltc2983 = adi.ltc2983(uri="local:")

print(ltc2983.channel["temp0"].raw)
print(ltc2983.channel["temp0"].value)

ltc2983.rx_buffer_size = 10
ltc2983.rx_enabled_channels = [0]

ltc2983.rx_output_type = "raw"
print(ltc2983.convert(0, ltc2983.rx()[0]))

ltc2983.rx_output_type = "SI"
print(ltc2983.rx()[0])
