# sw_5940_eit
Install prerequisites:
pip3 install -r requirements.txt

Run Bio Impedance measurements:
python3 query -h
This will display the help file

Examples:
Run Bio Impedance measurements on given electrodes:
python3 query.py -p com5 -z -e 0 3 1 2

In case the firmware is running an iio server:
python3 query.py -p com5 -b 230400 -z -e 0 3 1 2 --iio

This will Use Electrodes 0 and 3 for excitation ans electrodes 1 and 2 for sensing. -z tells the software to query impedance. Without -z, it will do voltage measurements.


To run the GUI:
python3 main.py -e 16

In case the firmware is running an iio server:
python3 main.py -b 230400 -e 16 --iio

This will start the GUI for the EIT. The GUI is currently a work in progress so there are a lot of know bugs which I will be fixing later.

