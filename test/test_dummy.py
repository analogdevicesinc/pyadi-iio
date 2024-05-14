import adi
import pytest
import test
import numpy as np
import pyvisa

import pyfirmata
import time

# def test_dummy():
#     x = 2
#     y = 3
#     assert x+y==5

    
def test_history():
    pytest.data= 1234

def test_history2():
    if hasattr(pytest, 'data'):
        print('found data')
        pytest.data = [5678, pytest.data]