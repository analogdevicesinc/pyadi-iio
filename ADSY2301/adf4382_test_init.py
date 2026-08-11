import adi
 
##############################################
## Step 1: Initialize ADAR1000 Array ##
##############################################
# talise_ip = "10.175.161.150"
talise_ip = "10.75.161.140"
talise_uri = "ip:" + talise_ip
 
#Initialize the ADF4382 LO
adf4382 = adi.adf4382(uri=talise_uri)
 
LO_Freq = int(14.9e9)
 
# # Configure pll attributes
# adf4382.sw_sync_en = 0  # Disable sync
# adf4382.reference_frequency = 122880000  # Input reference clock
# adf4382.reference_doubler_en = 1  # Enable reference doubler
# adf4382.reference_divider = 1  # Set reference divider
 
# adf4382.charge_pump_current = "11.100000"  # Set charge pump current in mA
 
adf4382.altvolt0_frequency = LO_Freq  # Output reference clock
adf4382.altvolt0_en = 1  # Enable output channel 0
# adf4382.altvolt0_output_power = 9  # Set output amplitude of ch. 0
 
adf4382.altvolt1_frequency = LO_Freq  # Output reference clock
adf4382.altvolt1_en = 1  # Enable output channel 1
# adf4382.altvolt1_output_power = 9  # Set output amplitude of ch. 1