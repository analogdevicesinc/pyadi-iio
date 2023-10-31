# Copyright (C) 2023 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import adi

dsa = adi.adrf5730(uri="ip:analog.local")

print(
    "---This example script produces attenuation values of 0, 4.0, 16.0 and 31.5 dB, corresponding to attenuation decimal values of 0, 8, 32 and 63, to be observed on the Spectrum Analyzer."
)

# Set GPIO attenuation of GPIO controlled DSA to 0 dB
dsa.GPIO_attenuation = 0
input(
    "Observe an attenuation of 0 dB = 0 decimal on the Spectrum Analyzer, press Enter to continue."
)

# Set GPIO attenuation of GPIO controlled DSA to 4.0 dB
dsa.GPIO_attenuation = 4.0
input(
    "Observe an attenuation of 4.0 dB = 8 decimal on the Spectrum Analyzer, press Enter to continue."
)

# Set GPIO attenuation of GPIO controlled DSA to 16.0 dB
dsa.GPIO_attenuation = 16.0
input(
    "Observe an attenuation of 16.0 dB  = 32 decimal on the Spectrum Analyzer, press Enter to continue."
)

# Set GPIO attenuation of GPIO controlled DSA to 31.5 dB
dsa.GPIO_attenuation = 31.5
input(
    "Observe an attenuation of 31.5 dB = 63 decimal on the Spectrum Analyzer, press Enter to end program."
)
