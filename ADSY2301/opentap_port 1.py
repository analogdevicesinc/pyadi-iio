import adi
import numpy as np
import time 
import 


def initalize_adars_local(self, pa_off=-4.8, pa_on=-4.8, lna_off=-4.8, lna_on=-0.9412):        
    self.reset()

    # Set the bias currents to nominal
    self.rx_lna_bias_current = 0x08
    self.rx_vga_vm_bias_current = 0x55
    self.tx_vga_vm_bias_current = 0x2D
    self.tx_pa_bias_current = 0x06

    # Disable RAM control
    self.beam_mem_enable = False
    self.bias_mem_enable = False
    self.common_mem_enable = False
    # Enable all internal amplifiers
    self.rx_vga_enable = True
    self.rx_vm_enable = True
    self.rx_lna_enable = True
    self.tx_vga_enable = True
    self.tx_vm_enable = True
    self.tx_pa_enable = True
    # Disable Tx/Rx paths for the device
    self.mode = "disabled"
    # Enable the PA/LNA bias DACs
    self.lna_bias_out_enable = True
    self.bias_dac_enable = True
    self.bias_dac_mode = "toggle"
    # Configure the external switch control
    self.external_tr_polarity = True
    self.tr_switch_enable = True
    # Set the default LNA bias
    self.lna_bias_off = lna_off
    self.lna_bias_on = lna_on

    # Settings for each channel
    for channel in self.channels:
        # Default channel enable            
        channel.rx_enable = False            
        channel.tx_enable = False
        # Default PA bias            
        channel.pa_bias_off = pa_off
        channel.pa_bias_on = pa_on

        # Default attenuator, gain, and phase            
        channel.rx_attenuator = False            
        channel.rx_gain = 0x7F
        channel.rx_phase = 0
        channel.tx_attenuator = False            
        channel.tx_gain = 0x7F
        channel.tx_phase = 0

    # Latch in the new settings
    self.latch_rx_settings()
    self.latch_tx_settings()
    self.mode = "rx"
    self.bias_dac_mode = "on"
    for channel in self.channels:
    # Default channel enable
        channel.rx_enable = True


    # 2: CONFIG RX
    # self.log.Info("ADAR1000 Channel " + str(self.Channel))
    self.ADAR1000.SetRxGain(self.Channel, self.gain)
    time.sleep(0.1)
    self.ADAR1000.SetRxAttenuation(self.Channel, self.attenuation)
    time.sleep(0.1)
    self.ADAR1000.SetRxPhase(self.Channel, self.phase)
    time.sleep(0.1)
    self.ADAR1000.SetLNAvoltage(self.Channel, self.lnaBias)
    time.sleep(0.1)
    self.ADAR1000.SetRxEnable(self.Channel, self.Enable)
    time.sleep(0.1)
    self.ADAR1000.dev.latch_rx_settings()
    time.sleep(0.1)

    print("ADAR1000 object initialized.")

##############################################
## Step 1: Initialize ADAR1000 Array ##
##############################################
talise_ip = "10.75.161.150"
talise_uri = "ip:" + talise_ip

# dev = adi.adar1000_array(
#     uri=talise_uri,

#     chip_ids=[
#         "adar1000_csb_1_1_1", "adar1000_csb_1_1_4", "adar1000_csb_1_2_1", "adar1000_csb_1_2_4",
#         "adar1000_csb_1_1_3", "adar1000_csb_1_1_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_2",
#         "adar1000_csb_0_1_1", "adar1000_csb_0_1_4", "adar1000_csb_0_2_1", "adar1000_csb_0_2_4",
#         "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2",
#     ],

#     device_map=[[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],

#     element_map=np.array([
#         [1,  9,  17, 25, 33, 41, 49, 57],
#         [2,  10, 18, 26, 34, 42, 50, 58],
#         [3,  11, 19, 27, 35, 43, 51, 59],
#         [4,  12, 20, 28, 36, 44, 52, 60],
#         [5,  13, 21, 29, 37, 45, 53, 61],
#         [6,  14, 22, 30, 38, 46, 54, 62],
#         [7,  15, 23, 31, 39, 47, 55, 63],
#         [8,  16, 24, 32, 40, 48, 56, 64],
#     ]),

#     device_element_map={
#         1:  [9, 10, 2, 1],     3:  [41, 42, 34, 33],
#         2:  [25, 26, 18, 17],  4:  [57, 58, 50, 49],
#         5:  [4, 3, 11, 12],    7:  [36, 35, 43, 44],
#         6:  [20, 19, 27, 28],  8:  [52, 51, 59, 60],
#         9:  [13, 14, 6, 5],    11: [45, 46, 38, 37],
#         10: [29, 30, 22, 21],  12: [61, 62, 54, 53],
#         13: [8, 7, 15, 16],    15: [40, 39, 47, 48],
#         14: [24, 23, 31, 32],  16: [56, 55, 63, 64],
#     },
# )

dev = adi.adar1000_array(
    uri=talise_uri,

    # chip_ids=[
    #     "adar1000_csb_1_1_1", "adar1000_csb_1_1_4", 
    #     "adar1000_csb_1_1_3", "adar1000_csb_1_1_2", 
    # ],

    chip_ids=[
        "adar1000_csb_0_1_1", "adar1000_csb_0_1_4", 
        "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", 
    ],

    device_map=[[1, 3, 2, 4]],

    element_map=np.array([
        [1,  5,  9, 13 ],
        [2,  6, 10, 14 ],
        [3,  7, 11, 15 ],
        [4,  8, 12, 16 ],

    ]),

    device_element_map={
        1:  [5, 6, 2, 1],     3:  [13, 14, 10, 9],
        2:  [4, 4, 7, 16],  4:  [12, 11, 15, 16],
    },
)
print("ADAR1000 array object created.")

# 1: INITIALIZE ADARs
for device in dev.devices.values():
    print(f"Initializing device {device.array_device_number}...")
    initalize_adars_local(device)

print("Done")