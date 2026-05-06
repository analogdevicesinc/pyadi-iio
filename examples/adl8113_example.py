# Copyright (C) 2026 Analog Devices, Inc.
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

import time

import adi

# Connect to ADL8113 device
# Modify the URI to match your setup
dev = adi.adl8113(uri="serial:/dev/ttyACM0,57600")

print("=" * 60)
print("ADL8113 RF Amplifier Example")
print("=" * 60)

# Demonstrate all available paths
# Note: External bypass gains must match your device tree configuration

print("\n1. Setting to Internal Amplifier (14 dB)")
dev.hardwaregain = 14
print(f"   Current gain: {dev.hardwaregain} dB")
time.sleep(1)

print("\n2. Setting to Internal Bypass (-2 dB)")
dev.hardwaregain = -2
print(f"   Current gain: {dev.hardwaregain} dB")
time.sleep(1)

# External bypass examples (uncomment if configured in your device tree)
print("\n3. Setting to External Bypass A (example: 1 dB)")
dev.hardwaregain = 1  # Replace 1 with your configured gain
print(f"   Current gain: {dev.hardwaregain} dB")
time.sleep(1)

print("\n4. Setting to External Bypass B (example: 2 dB)")
dev.hardwaregain = 2  # Replace 2 with your configured gain
print(f"   Current gain: {dev.hardwaregain} dB")
time.sleep(1)

print("\n" + "=" * 60)
print("Interactive Mode")
print("=" * 60)

try:
    while True:
        gain_str = input("\nEnter desired gain in dB (or 'q' to quit): ").strip()

        if gain_str.lower() == "q":
            break

        try:
            gain_value = int(gain_str)
            dev.hardwaregain = gain_value
            print(f"Hardware gain set to: {dev.hardwaregain} dB")
        except ValueError:
            print("Error: Please enter a valid integer")
        except Exception as e:
            print(f"Error: {e}")
            print("Valid gains: 14, -2, and any configured external bypass gains")

except KeyboardInterrupt:
    print("\n\nExiting...")
