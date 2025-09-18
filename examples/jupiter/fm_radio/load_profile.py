import adi


# Load stream and profile
dev = adi.adrv9002(uri="ip:analog.local")
root_name = "fm_768k_fdd"
dev.write_stream_profile(f"{root_name}.bin", f"{root_name}.json")

assert dev.rx0_sample_rate == 768000
assert dev.tx0_sample_rate == 768000

del dev