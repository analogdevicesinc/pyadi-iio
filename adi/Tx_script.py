import adi
import paramiko
import time
import MantaRay as mr
import numpy as np

print("Set PA_ON to 0")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")
time.sleep(1)
ssh.close()


print("Turn on 4V, then -6V supplies")
input("Press Enter to continue...")
talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

print("Connecting to BFC Tile")


dev = adi.adar1000_array(
    "ip:192.168.1.1", 
    chip_ids= 	[	
                    "adar1000_csb_0_1_1", "adar1000_csb_0_1_2", "adar1000_csb_0_1_3", "adar1000_csb_0_1_4",
                    "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
                    "adar1000_csb_0_2_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
                    "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"
                ],
    device_map=	[
                    [2, 1], 
                    [3, 4],
                    [6, 5], 
                    [7, 8],
                    [10, 9],
                    [11, 12],
                    [14, 13],
                    [15, 16],
                ],
    element_map=[
                    [1, 2, 3, 4], 
                    [5, 6, 7, 8], 
                    [9, 10, 11, 12], 
                    [13, 14, 15, 16],
                    [17, 18, 19, 20], 
                    [21, 22, 23, 24], 
                    [25, 26, 27, 28], 
                    [29, 30, 31, 32],
                    [33, 34, 35, 36], 
                    [37, 38, 39, 40], 
                    [41, 42, 43, 44], 
                    [45, 46, 47, 48],
                    [49, 50, 51, 52], 
                    [53, 54, 55, 56], 
                    [57, 58, 59, 60], 
                    [61, 62, 63, 64],
                ],
    device_element_map={
                1: 	[4, 8, 7, 3],
                2: 	[2, 6, 5, 1],
                3: 	[13, 9, 10, 14],
                4: 	[15, 11, 12, 16],
                5: 	[20, 24, 23, 19],
                6: 	[18, 22, 21, 17],
                7: 	[29, 25, 26, 30],
                8: 	[31, 27, 28, 32],
                9: 	[36, 40, 39, 35],
                10: 	[34, 38, 37, 33],
                11: 	[45, 41, 42, 46],
                12: 	[48, 44, 43, 47],
                13: 	[52, 56, 55, 51],
                14: 	[50, 54, 53, 49],
                15: 	[61, 57, 58, 62],
                16: 	[64, 60, 59, 63],
    },
)


for device in dev.devices.values():
    device.tr_source = "spi"
    
print("Connected to BFC Tile")

mr.disable_stingray_channel(dev)

print("Initializing BFC Tile")
dev.initialize_devices(-4.6, -4.6, -4.6, -4.6)
for device in dev.devices.values():
    device.mode = "rx"
    device.bias_dac_mode = "on"
    for channel in device.channels:
        # Default channel enable
        channel.rx_enable = True
print("Initialized BFC Tile")


print("Turn on 5.7V, current should be ~100mA")
input("Press Enter to continue...")


print("Turn on 18V, current should be ~1mA")
input("Press Enter to continue...")

# subarray_ref = np.array([1, 17, 52, 45])
subarray_ref = np.array([4, 36, 52, 20])


for i in subarray_ref:
    time.sleep(0.25)
    print("Setting element " + str(i) + " gain max")
    dev.elements[i].tx_gain = 127
    print("Setting element " + str(i) + " attenuator off")
    dev.elements[i].tx_attenuator = False
    print("Setting element " + str(i) + " phase 0")
    dev.elements[i].tx_phase = 0
    print("Setting element " + str(i) + " PA bias to -2.2")
    dev.elements[i].pa_bias_on = -2.2
    print("Setting element " + str(i) + " Tx Enable")
    dev.elements[i].tx_enable = True
    print("Setting Adar " + str(i) + " TR Source")
    for device in dev.devices.values():
        device.tr_source = "external"
        device.bias_dac_mode = "toggle"
    print("Load Tx Setting")
    dev.latch_tx_settings()


# for i in range(32):
#     i = i + 1
#     time.sleep(0.25)
#     print("Setting element " + str(i) + " gain max")
#     dev.elements[i].tx_gain = 127
#     print("Setting element " + str(i) + " attenuator off")
#     dev.elements[i].tx_attenuator = False
#     print("Setting element " + str(i) + " phase 0")
#     dev.elements[i].tx_phase = 0
#     print("Setting element " + str(i) + " PA bias to -2")
#     dev.elements[i].pa_bias_on = -2.0

#     print("Setting element " + str(i) + " Tx Enable")
#     dev.elements[i].tx_enable = True
#     print("Setting Adar " + str(i) + " TR Source")
#     for device in dev.devices.values():
#         device.tr_source = "external"
#         device.bias_dac_mode = "toggle"
#     print("Load Tx Setting")
#     dev.latch_tx_settings()


# print("Setting element 1 gain max")
# dev.elements[1].tx_gain = 127
# print("Setting element 1 attenuator off")
# dev.elements[1].tx_attenuator = False
# print("Setting element 1 phase 0")
# dev.elements[1].tx_phase = 0
# print("Setting element 1 PA bias to -2")
# dev.elements[1].pa_bias_on = -2
# print("Setting element 1 Tx Enable")
# dev.elements[1].tx_enable = True
# print("Setting Adar 1 TR Source")
# for device in dev.devices.values():
#     device.tr_source = "external"
#     device.bias_dac_mode = "toggle"
# print("Load Tx Setting")
# dev.latch_tx_settings()


print("Set PA_ON to 1")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 1")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 1")
time.sleep(1)
ssh.close()


print("Turn on Function Generator")
input("Press Any key to turn off PA_ON and quit...")
print("Set PA_ON to 0")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")
time.sleep(1)
ssh.close()