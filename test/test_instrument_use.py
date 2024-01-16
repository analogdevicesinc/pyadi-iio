import pytest

@pytest.mark.skip(reason="No instrument connected")
def test_e36233a():
    from .instruments import E36233A
    psu = E36233A()