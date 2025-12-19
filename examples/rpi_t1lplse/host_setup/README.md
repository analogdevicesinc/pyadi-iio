# AD-RPI-T1LPSE-SL Temperature Controller System Setup

Required:
- 1x Raspberry Pi 4 Model B
- 1x AD-RPI-T1LPSE-SL Board
- 2x AD-SWIOT1L-SL Boards
- 1x Fan Actuator
- 1x TMP01 Temperature Sensor
- 1x MAX32625PICO programmer/debugger
- 1x Raspberry Pi charger (5V, 3A minimum)

## Update the firmware on the AD-SWIOT1L-SL boards
Each AD-SWIOT1L-SL must be updated with the provided firmware image.

1. Follow the official update instructions <a href=https://analogdevicesinc.github.io/documentation/solutions/reference-designs/ad-swiot1l-sl/software-guide/index.html#updating-the-ad-swiot1l-sl-firmware>here</a>.

2. Repeat the process for both boards.

3. Use the firmware images provided in the current folder. They configure the boards with static IP addresses:
        - The first board will have the ```192.168.97.40``` IP address
        - The second board will have the ```192.168.97.41``` IP address

4. After flashing, verify that each board responds to ping:
``` 
ping 192.168.97.40
ping 192.168.97.41
```

## Configure the Network on Raspberry Pi
The Raspberry Pi must be configured to communicate with both AD-SWIOT1L-SL boards.

1. From the project folder, navigate to the host_setup directory.

2. Copy the connection profiles into NetworkManager’s system folder:
```
sudo cp -v "Wired connection 2" /etc/NetworkManager/system-connections/
sudo cp -v "Wired connection 3" /etc/NetworkManager/system-connections/
```

3. Ensure correct permissions:
``` 
sudo chmod 600 /etc/NetworkManager/system-connections/Wired\ connection\ 2
sudo chmod 600 /etc/NetworkManager/system-connections/Wired\ connection\ 3
```

4. Reload NetworkManager:
```
sudo nmcli connection reload
```

5. Verify the connections are active:
```
nmcli connection show
```
