import os
import sys

# Add parent directory to path so MR package can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MR.CONV
import MR.BFC

if __name__ == "__main__":

    #Initialize the SDR
    MR.CONV.DAC_TDD_Config.sdr_init()

    #Initialize the TDD Engine
    MR.CONV.DAC_TDD_Config.tdd_init()

    #Initialize the ADSY2301
    MR.BFC.ADSY2301_Init.init_adsy2301()