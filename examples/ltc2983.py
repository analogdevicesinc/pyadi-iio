import adi

ltc2983 = adi.ltc2983(uri="local:")

print(ltc2983.channel["temp0"].raw)
print(ltc2983.channel["temp0"].value)

vals = [ltc2983.channel["temp0"].raw for _ in range(10)]
print(ltc2983.convert("temp0", vals))
print(ltc2983.convert(0, vals))
