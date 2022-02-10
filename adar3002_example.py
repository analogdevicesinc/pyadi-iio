import adi

bf = adi.adar3002("ip:10.72.162.61",driver_name="adar3002_T0")
bfa = adi.adar3002_array("ip:10.72.162.61")

# a = bf.amp_en_mute_ELV
# a['adar3002_csb_0_0'] = [0,0,0,0]
# a= [0,0,0,1 ,0,0,0,0]
# bf.amp_en_mute_ELV = a

# bf.annotated_properties = True
# print(bf.__repr__())