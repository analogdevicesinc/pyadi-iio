import adi

def set_filter_settings(hp_freq, lp_freq):
    HPF_state = int((hp_freq/1e9 - 6.4) / 0.333 + 0.5)
    LPF_state = int((lp_freq/1e9 - 7.2) / 0.34 + 0.5)

    hpf_actual = 6.4 + HPF_state * 0.333
    lpf_actual = 7.2 + LPF_state * 0.34

    print(f"Requested: HPF = {hp_freq/1e9} GHz, LPF = {lp_freq/1e9} GHz")
    print(f"Nearest: HPF = {hpf_actual:.1f} GHz (state {HPF_state}), "f"LPF = {lpf_actual:.1f} GHz (state {LPF_state})")

    hpf_bits = [(HPF_state >> i) & 1 for i in range(4)]
    lpf_bits = [(LPF_state >> i) & 1 for i in range(4)]

    print(f"Setting HPF bits: "f"B3={hpf_bits[3]} B2={hpf_bits[2]} "f"B1={hpf_bits[1]} B0={hpf_bits[0]}")
    RF_FL_HPF0._attrs["raw"].value = str(hpf_bits[0])
    RF_FL_HPF1._attrs["raw"].value = str(hpf_bits[1])
    RF_FL_HPF2._attrs["raw"].value = str(hpf_bits[2])
    RF_FL_HPF3._attrs["raw"].value = str(hpf_bits[3])

    print(f"Setting LPF bits: "f"B3={lpf_bits[3]} B2={lpf_bits[2]} "f"B1={lpf_bits[1]} B0={lpf_bits[0]}")
    RF_FL_LPF0._attrs["raw"].value = str(lpf_bits[0])
    RF_FL_LPF1._attrs["raw"].value = str(lpf_bits[1])
    RF_FL_LPF2._attrs["raw"].value = str(lpf_bits[2])
    RF_FL_LPF3._attrs["raw"].value = str(lpf_bits[3])

talise_ip = "10.75.161.151"
#talise_ip = "10.75.161.140"
talise_uri = "ip:" + talise_ip

dev = adi.adrv9009_zu11eg(uri=talise_uri)

artix_control = dev.ctx.find_device("mantaray_control")
talise_control = dev.ctx.find_device("mantaray_talise_control")
switch = dev.ctx.find_device("mantaray_txrx_control")

for channel in artix_control.channels:
    if channel.attrs["label"].value == "RF_FL_HPF0":
        RF_FL_HPF0 = artix_control.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "RF_FL_HPF1":
        RF_FL_HPF1 = artix_control.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "RF_FL_HPF2":
        RF_FL_HPF2 = artix_control.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "RF_FL_HPF3":
        RF_FL_HPF3 = artix_control.find_channel(channel.id, True)

    elif channel.attrs["label"].value == "RF_FL_LPF0":
        RF_FL_LPF0 = artix_control.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "RF_FL_LPF1":
        RF_FL_LPF1 = artix_control.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "RF_FL_LPF2":
        RF_FL_LPF2 = artix_control.find_channel(channel.id, True)
    elif channel.attrs["label"].value == "RF_FL_LPF3":
        RF_FL_LPF3 = artix_control.find_channel(channel.id, True)

    else:
        pass


hp_freq = 7.9e9
lp_freq = 13e9
set_filter_settings(hp_freq, lp_freq)