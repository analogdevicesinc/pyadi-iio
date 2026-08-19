import adi

#TX Functions 

def TX_0_SW_Enable():
    ADRF5030_EN1._attrs["raw"].value = "0"
    ADRF5030_CTRL1._attrs["raw"].value = "1"

def TX_1_SW_Enable():
    ADRF5030_EN2._attrs["raw"].value = "0"
    ADRF5030_CTRL2._attrs["raw"].value = "1"

def TX_2_SW_Enable():
    ADRF5030_EN3._attrs["raw"].value = "0"
    ADRF5030_CTRL3._attrs["raw"].value = "1"

def TX_3_SW_Enable():
    ADRF5030_EN4._attrs["raw"].value = "0"
    ADRF5030_CTRL4._attrs["raw"].value = "1"

#RX Functions 

def RX_0_SW_Enable():
    ADRF5030_EN1._attrs["raw"].value = "0"
    ADRF5030_CTRL1._attrs["raw"].value = "0"

def RX_1_SW_Enable():
    ADRF5030_EN1._attrs["raw"].value = "0"
    ADRF5030_CTRL1._attrs["raw"].value = "0"

def RX_2_SW_Enable():
    ADRF5030_EN1._attrs["raw"].value = "0"
    ADRF5030_CTRL1._attrs["raw"].value = "0"

def RX_3_SW_Enable():
    ADRF5030_EN1._attrs["raw"].value = "0"
    ADRF5030_CTRL1._attrs["raw"].value = "0"


talise_ip = "10.75.161.151"
#talise_ip = "10.75.161.140"
talise_uri = "ip:" + talise_ip

dev = adi.adrv9009_zu11eg(uri=talise_uri)

artix_control = dev.ctx.find_device("mantaray_control")
talise_control = dev.ctx.find_device("mantaray_talise_control")
switch = dev.ctx.find_device("mantaray_txrx_control")

for channel in artix_control.channels:
    if channel.attrs["label"].value == "ADRF5030_CTRL1":
        ADRF5030_CTRL1 = switch.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "ADRF5030_CTRL2":
        ADRF5030_CTRL2 = switch.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "ADRF5030_CTRL3":
        ADRF5030_CTRL3 = switch.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "ADRF5030_CTRL4":
        ADRF5030_CTRL4 = switch.find_channel(channel.id, True)

    if channel.attrs["label"].value == "ADRF5030_EN1":
        ADRF5030_EN1 = switch.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "ADRF5030_EN2":
        ADRF5030_EN2 = switch.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "ADRF5030_EN3":
        ADRF5030_EN3 = switch.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "ADRF5030_EN4":
        ADRF5030_EN4 = switch.find_channel(channel.id, True)

    else:
        pass

RX = True
TX = False

if RX:
    #RX Setup:
    RX_0_SW_Enable()
    RX_1_SW_Enable()
    RX_2_SW_Enable()
    RX_3_SW_Enable()
    print("RX Switches Enabled")

if TX:
    #TX Setup:
    TX_0_SW_Enable()
    TX_1_SW_Enable()
    TX_2_SW_Enable()
    TX_3_SW_Enable()
    print("TX Switches Enabled")