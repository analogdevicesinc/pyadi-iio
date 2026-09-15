# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi


def main():
    # get comport from command line or use default
    uri = sys.argv[1] if len(sys.argv) > 1 else "serial:COM149,115200,8n1"

    print(f"Connecting to MAXM86161 at: {uri}")
    dev = adi.maxm86161(uri=uri)

    print("\n--- Device Info ---")
    print(f"Part ID: {dev.part_id}")
    print(f"Rev ID: {dev.rev_id}")
    print(f"Interrupt Status: {dev.interrupt_status}")
    print(f"Die Temperature (u-degC): {dev.die_temperature}")

    print("\n--- FIFO Configuration ---")
    dev.fifo_watermark = 15
    dev.fifo_rollover = 1
    dev.fifo_a_full_type = 0
    print(f"Watermark: {dev.fifo_watermark}")
    print(f"Rollover: {dev.fifo_rollover}")
    print(f"A_FULL Type: {dev.fifo_a_full_type}")
    print(f"FIFO Count: {dev.fifo_count}")

    print("\n--- PPG Configuration ---")
    dev.sample_rate = 0  # sample-rate selection code
    dev.integration_time = 3  # 117.3 us
    dev.adc_range = 2  # 16 uA full-scale
    dev.sample_averaging = 1  # average 2 samples per FIFO point
    dev.alc_disable = 0  # ambient-light cancellation enabled
    dev.add_offset = 0
    dev.led_settling = 2  # 8 us
    dev.dig_filter = 0  # CDM
    dev.pd_bias = 1  # 0-65 pF photodiode
    print(f"Sample Rate: {dev.sample_rate}")
    print(f"Integration Time: {dev.integration_time}")
    print(f"ADC Range: {dev.adc_range}")
    print(f"Sample Averaging: {dev.sample_averaging}")
    print(f"Digital Filter: {dev.dig_filter}")

    # LED drive config (green=1, IR=2, red=3)
    print("\n--- LED Drive Configuration ---")
    dev.set_led_range(1, 1)  # green: 62 mA range
    dev.set_led_pa(1, 128)  # green: mid-scale pulse amplitude
    dev.set_led_range(2, 1)  # IR: 62 mA range
    dev.set_led_pa(2, 100)  # IR: pulse amplitude
    dev.set_led_range(3, 1)  # red: 62 mA range
    dev.set_led_pa(3, 100)  # red: pulse amplitude
    print(f"LED1 (green) PA: {dev.get_led_pa(1)}, range: {dev.get_led_range(1)}")
    print(f"LED2 (IR)    PA: {dev.get_led_pa(2)}, range: {dev.get_led_range(2)}")
    print(f"LED3 (red)   PA: {dev.get_led_pa(3)}, range: {dev.get_led_range(3)}")

    # LED exposure sequence (up to 6 slots)
    print("\n--- LED Exposure Sequence ---")
    dev.set_led_sequence(1, 1)  # slot 1: green
    dev.set_led_sequence(2, 2)  # slot 2: IR
    dev.set_led_sequence(3, 3)  # slot 3: red
    dev.set_led_sequence(4, 0)  # slot 4: none
    dev.set_led_sequence(5, 0)  # slot 5: none
    dev.set_led_sequence(6, 0)  # slot 6: none
    for slot in range(1, 7):
        print(f"Sequence slot {slot}: {dev.get_led_sequence(slot)}")

    # Capture PPG data
    print("\n--- Capturing PPG Data ---")
    dev.rx_buffer_size = 128
    dev.buffer_enable = 1  # exit shutdown and start capture

    num_captures = 5
    for i in range(num_captures):
        data = dev.rx()
        # each sample packs a 5-bit tag [23:19] with the 19-bit value [18:0]
        tags = [(s >> 19) & 0x1F for s in data]
        values = [s & 0x7FFFF for s in data]
        print(
            f"Capture {i + 1}: {len(data)} samples, "
            f"min={min(values)}, max={max(values)}, "
            f"avg={sum(values) / len(values):.1f}, "
            f"tags={sorted(set(tags))}"
        )
        time.sleep(0.1)

    dev.buffer_enable = 0  # stop capture, re-enter shutdown

    print("\n--- Final Status ---")
    print(f"FIFO Count: {dev.fifo_count}")
    print(f"FIFO Overflow Count: {dev.fifo_overflow_count}")
    print(f"Interrupt Status: {dev.interrupt_status}")

    print("\nDone.")


if __name__ == "__main__":
    main()
