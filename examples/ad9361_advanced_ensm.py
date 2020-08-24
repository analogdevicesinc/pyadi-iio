import adi

# This example shows how to navigate between FDD and TDD modes using debug attributes for AD936X devices

sdr = adi.ad9361(uri="ip:analog")

# Initial stage
print("Initial ensm_mode:", sdr._ctrl.attrs["ensm_mode"].value)

# Get to TDD mode
sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "0"
sdr._ctrl.debug_attrs["initialize"].value = "1"
print("ensm_mode_available:", sdr._ctrl.attrs["ensm_mode_available"].value)
print("Current ensm:", sdr._ctrl.attrs["ensm_mode"].value)

# Get to FDD mode
sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
# Disable pin control so spi can move the states
sdr._ctrl.debug_attrs["adi,ensm-enable-txnrx-control-enable"].value = "0"
sdr._ctrl.debug_attrs["initialize"].value = "1"
print("ensm_mode_available:", sdr._ctrl.attrs["ensm_mode_available"].value)
print("Current ensm:", sdr._ctrl.attrs["ensm_mode"].value)
