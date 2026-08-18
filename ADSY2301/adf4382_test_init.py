import adi
 
##############################################
## Step 1: Initialize ADAR1000 Array ##
##############################################
talise_ip = "10.75.161.150"
#talise_ip = "10.75.161.140"
talise_uri = "ip:" + talise_ip
 
#Initialize the ADF4382 LO
LO = adi.adf4382(uri=talise_uri)

print("Current Settings:") 
print("LO Frequency Channel 0: ", LO.altvolt0_frequency)
print("LO Frequency Channel 1: ", LO.altvolt1_frequency)

print("LO Phase Channel 0: ", LO.altvolt0_phase)
print("LO Phase Channel 1: ", LO.altvolt1_phase)

print("LO Channel 0 Enable: ", LO.altvolt0_en)
print("LO Channel 1 Enable: ", LO.altvolt1_en)

print("LO Channel 0 Bleed Polarity: ", LO.altvolt0_bleed_pol)
print("LO Channel 1 Bleed Polarity: ", LO.altvolt1_bleed_pol)

print("LO Channel 0 Auto Align: ", LO.altvolt0_en_auto_align)
print("LO Channel 1 Auto Align: ", LO.altvolt1_en_auto_align)

print("LO Channel 0 Hardware Gain: ", LO.altvolt0_hardwaregain)
print("LO Channel 1 Hardware Gain: ", LO.altvolt1_hardwaregain)

print("LO Channel 0 fine current: ", LO.altvolt0_fine_current)
print("LO Channel 1 fine current: ", LO.altvolt1_fine_current)

print("LO Channel 0 coarse current: ", LO.altvolt0_coarse_current)
print("LO Channel 1 coarse current: ", LO.altvolt1_coarse_current)

LO_Freq = int(14.9e9)

print("Setting LO Frequency to %2.2f GHz" % (LO_Freq//1e9))

LO.altvolt0_frequency = LO_Freq
LO.altvolt1_frequency = LO_Freq
