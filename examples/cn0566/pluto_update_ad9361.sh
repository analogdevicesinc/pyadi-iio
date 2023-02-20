#!/bin/bash

echo "Setting Pluto to AD9361, 2r2t mode..."

rm ~/.ssh/known_hosts # Changes with each Pluto, clear
sshpass -p 'analog' ssh -o StrictHostKeyChecking=no root@pluto.local 'fw_setenv attr_name compatible'
sshpass -p 'analog' ssh -o StrictHostKeyChecking=no root@pluto.local 'fw_setenv attr_val ad9361'
sshpass -p 'analog' ssh -o StrictHostKeyChecking=no root@pluto.local 'fw_setenv compatible ad9361'
sshpass -p 'analog' ssh -o StrictHostKeyChecking=no root@pluto.local 'fw_setenv mode 2r2t'
sshpass -p 'analog' ssh -o StrictHostKeyChecking=no root@pluto.local 'reboot'

echo "Done setting parameters, wait for Pluto to reboot (heartbeat light restarts)"

exit
