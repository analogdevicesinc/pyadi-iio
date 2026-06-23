import pytest

import adi

hardware = ["adg2128"]
classname = "adi.adg2128"


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize(
    "addr1, addr2", [(0x71, 0x70),],
)
def test_adg2128(context_desc, addr1, addr2):
    cps = None
    for ctx_desc in context_desc:
        if ctx_desc["hw"] in hardware:
            cps = adi.adg2128(uri=ctx_desc["uri"])
            break
    if cps is None:
        pytest.skip("No valid hardware found")

    cps.add(addr1)
    cps.add(addr2)

    cps[0][0] = True
    assert cps[0][0] == True
    cps[0][0] = False
    assert cps[0][0] == False
    cps[23][7] = True
    assert cps[23][7] == True
    cps[23][7] = False
    assert cps[23][7] == False
