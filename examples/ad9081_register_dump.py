import adi

uri = "ip:analog.local"
sdr = adi.ad9081(uri)
ctx = sdr._ctx
dev = ctx.find_device("axi-ad9081-rx-hpc")

# Select components of interest
adc = 2  # Can be 0,1,2,3 (0,1 for AD9082)
cddc = 0  # Can be 0,1,2,3
fddc = 0  # Can be 0,1,2,3,4,5,6,7
jtx = 0  # Can be 0,1 (Link 0, Link 1)
dac = 0  # Can be 0,1,2,3
fduc = 0  # Can be 0,1,2,3,4,5,6,7

# RX
ADC_COARSE_PAGE = 0x18
FINE_DDC_PAGE = 0x19
JTX_PAGE = 0x1A

# TX
PAGEINDX_DAC_MAINDP_DAC = 0x1B
PAGEINDX_DAC_CHAN = 0x1C

# Paging helpers
def set_bit(val, index, bit):
    # print('{:b}'.format(val))
    mask = 1 << index
    val &= ~mask
    if bit:
        val |= mask
    # print('{:b}'.format(val))
    return val


def set_page(reg, numbits, bit_to_set, offset):
    val = dev.reg_read(reg)
    for k in range(numbits):
        val = set_bit(val, k + offset, k == bit_to_set)
    dev.reg_write(reg, val)
    rval = dev.reg_read(reg)
    assert val == rval


## ADC
set_page(ADC_COARSE_PAGE, 4, adc, 0)

## CDDC
set_page(ADC_COARSE_PAGE, 4, cddc, 4)

## FDDC
set_page(FINE_DDC_PAGE, 8, fddc, 0)

## JTX
set_page(JTX_PAGE, 2, jtx, 0)

## DAC/CDUC
set_page(PAGEINDX_DAC_MAINDP_DAC, 4, dac, 0)

## FDUC
set_page(PAGEINDX_DAC_CHAN, 8, fduc, 0)


### Dump all registers
def do_dump(filename):
    start = 0x0
    last = 0x3D26

    reg = start
    with open(filename, "w") as log:
        log.write("Register,Value\n")
        while reg <= last:
            hex_string = hex(dev.reg_read(reg))
            l = f"{hex(reg)},{hex_string}"
            print(l)
            log.write(l + "\n")
            reg += 1


##### Check all registers between changes
sdr.rx_nyquist_zone = ["even", "even", "even", "even"]
do_dump("reg1.log")
sdr.rx_nyquist_zone = ["odd", "odd", "odd", "odd"]
do_dump("reg2.log")

##### Check Nyquist alone
reg = 0x2110  # NYQUIST_ZONE_SELECT
sdr.rx_nyquist_zone = ["even", "even", "even", "even"]
pre_reg = dev.reg_read(reg)

sdr.rx_nyquist_zone = ["odd", "odd", "odd", "odd"]
post_reg = dev.reg_read(reg)

print([hex(pre_reg), hex(post_reg)])
print("{:b} {:b}".format(pre_reg, post_reg))
