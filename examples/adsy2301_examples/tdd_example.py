from adi import adsy2301 as mr


talise_ip = "10.75.161.151"
talise_uri = "ip:" + talise_ip

dev = mr.adsy2301(uri=talise_uri)
dev.init_ADRV9009()
# dev.init_BFC()
mr.tdd_init(dev,TXRX_Bit=0)

print(True)