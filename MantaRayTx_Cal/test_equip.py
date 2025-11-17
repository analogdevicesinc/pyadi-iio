import N6705B_Driver as N6705B
import pyvisa
import psutil
import zeroconf
import E36233A_Driver as E36233A
rm = pyvisa.ResourceManager()
# print(rm.list_resources())
N67 = "TCPIP::192.168.1.35::inst0::INSTR"
Pwr_Supplies = E36233A.E36233A(rm, N67)

Pwr_Supplies.output_on(1)
Pwr_Supplies.set_voltage(1,2)
print(Pwr_Supplies.get_voltage_setting(1))
print(Pwr_Supplies.measure_voltage(1))
print(Pwr_Supplies.measure_current(1))


Pwr_Supplies.set_voltage(4,4)
Pwr_Supplies.set_voltage(2,-6)