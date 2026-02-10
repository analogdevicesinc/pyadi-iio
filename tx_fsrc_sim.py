#!/usr/bin/env python3
"""
TX FSRC (Fractional Sample Rate Converter) Python Simulation

This simulation models the FPGA TX FSRC datapath from the AD9084 testbench,
including:
- Accumulator-based sample enable generation
- Hole insertion for fractional sample rate conversion
- JESD204 transport layer mapping

Based on: ADS10v1/AD9084_ADS10v1_Acorn/trunk/fpga_ip/datapath_tx/fpga_src/sim/tb_tx_fsrc.sv
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FSRCConfig:
    """Configuration parameters for the TX FSRC simulation."""
    # Core parameters
    np_bits: int = 16           # Bits per sample (N')
    data_width: int = 256       # Total data width per converter
    max_conv: int = 4           # Maximum number of converters
    accum_width: int = 64       # Accumulator width

    # JESD parameters
    jesd_l: int = 8             # Number of lanes
    jesd_m: int = 2             # Number of converters
    jesd_f: int = 1             # Octets per frame
    jesd_s: int = 2             # Samples per frame per converter (derived from L*F*8/(M*NP))
    jesd_np: int = 16           # Bits per sample
    num_links: int = 1          # Number of JESD links (1 or 2)

    # FSRC parameters
    channel_to_sample_rate_ratio: float = 0.6666667  # N/M ratio
    ns: int = 1                 # Number of samples grouped together

    # Simulation parameters
    random_data: bool = False
    identical_data: bool = True
    always_ready: bool = True
    always_valid: bool = True

    @property
    def num_samples(self) -> int:
        """Number of samples per clock cycle."""
        return self.data_width // self.np_bits

    @property
    def conv_mask(self) -> int:
        """Converter mask based on JESD M parameter."""
        return (1 << self.jesd_m) - 1

    @property
    def fsrc_invalid_sample(self) -> int:
        """Invalid sample marker (MSB set, rest zeros)."""
        return 1 << (self.np_bits - 1)

    @property
    def one_fixed(self) -> int:
        """Fixed-point representation of 1.0."""
        return 1 << self.accum_width

    @property
    def ratio_fixed(self) -> int:
        """Fixed-point representation of channel-to-sample rate ratio."""
        return int(self.one_fixed * self.channel_to_sample_rate_ratio)


class Accumulator:
    """
    Fixed-point accumulator with set and overflow detection.

    Models: accum_set.sv
    """

    def __init__(self, width: int = 64):
        self.width = width
        self.mask = (1 << width) - 1
        self.accum = 0
        self.overflow = False

    def set(self, value: int) -> None:
        """Set accumulator to a specific value."""
        self.accum = value & self.mask
        self.overflow = False

    def add(self, value: int) -> bool:
        """Add value to accumulator, return True if overflow occurred."""
        result = self.accum + value
        self.overflow = result > self.mask
        self.accum = result & self.mask
        return self.overflow

    def reset(self) -> None:
        """Reset accumulator to zero."""
        self.accum = 0
        self.overflow = False


class SampleEnableGenerator:
    """
    Generates sample enable signals based on accumulator overflow.

    Models: tx_fsrc_sample_en_gen.sv

    The accumulators determine which sample positions should contain
    valid data vs. "holes" (invalid samples) for fractional rate conversion.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.accumulators = [Accumulator(config.accum_width)
                            for _ in range(config.num_samples)]
        self._compute_initial_values()

    def _compute_initial_values(self) -> None:
        """Compute initial accumulator values based on config."""
        self.initial_values = []
        ratio_fixed = self.config.ratio_fixed
        one_fixed = self.config.one_fixed

        for i in range(self.config.num_samples):
            ns_group = i // self.config.ns
            # Initial value = ONE - RATIO + (group * RATIO)
            val = (one_fixed - ratio_fixed + (ns_group * ratio_fixed)) & ((1 << self.config.accum_width) - 1)
            self.initial_values.append(val)
            logger.debug(f"Accumulator {i} initial value: 0x{val:016X}")

    def set_accumulators(self) -> None:
        """Set all accumulators to their initial values."""
        for i, accum in enumerate(self.accumulators):
            accum.set(self.initial_values[i])

    def step(self, enable: bool = True) -> np.ndarray:
        """
        Advance accumulators by one cycle.

        Returns:
            Array of sample enable flags (True = valid sample, False = hole)
        """
        sample_en = np.zeros(self.config.num_samples, dtype=bool)

        if enable:
            for i, accum in enumerate(self.accumulators):
                sample_en[i] = accum.add(self.config.ratio_fixed)

        return sample_en


class HoleInserter:
    """
    Inserts invalid samples (holes) into the data stream.

    Models: tx_fsrc_make_holes.sv

    Takes a stream of valid input samples and inserts holes at positions
    where sample_en is False, using a buffering scheme to handle the
    variable input/output rates.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.data_buffer = [deque() for _ in range(config.max_conv)]
        self.pending_output = None
        self.holes_buffer = deque()

    def reset(self) -> None:
        """Reset internal state."""
        for buf in self.data_buffer:
            buf.clear()
        self.holes_buffer.clear()
        self.pending_output = None

    def input_samples(self, data: np.ndarray, valid: bool = True) -> None:
        """
        Input samples into the buffer.

        Args:
            data: Array of shape (num_conv, num_samples) containing sample data
            valid: Whether input data is valid
        """
        if valid:
            for conv_idx in range(min(data.shape[0], self.config.max_conv)):
                for sample in data[conv_idx]:
                    self.data_buffer[conv_idx].append(sample)

    def can_output(self, holes: np.ndarray) -> bool:
        """Check if enough samples are buffered to produce output."""
        # Count non-holes (valid sample positions needed)
        needed = np.sum(~holes)
        # Check if all active converters have enough samples
        for conv_idx in range(self.config.jesd_m):
            if len(self.data_buffer[conv_idx]) < needed:
                return False
        return True

    def output_samples(self, holes: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate output with holes inserted.

        Args:
            holes: Boolean array where True indicates a hole position

        Returns:
            Array of shape (num_conv, num_samples) with holes inserted,
            or None if not enough data buffered
        """
        if not self.can_output(holes):
            return None

        output = np.zeros((self.config.max_conv, self.config.num_samples),
                         dtype=np.uint64)

        for conv_idx in range(self.config.jesd_m):
            for sample_idx in range(self.config.num_samples):
                if holes[sample_idx]:
                    output[conv_idx, sample_idx] = self.config.fsrc_invalid_sample
                else:
                    if self.data_buffer[conv_idx]:
                        output[conv_idx, sample_idx] = self.data_buffer[conv_idx].popleft()
                    else:
                        output[conv_idx, sample_idx] = self.config.fsrc_invalid_sample

        return output


class JESDTransportLayer:
    """
    JESD204 Transport Layer simulation.

    Models: jtx_transport_single_link.sv and jtx_transport_dual_link.sv

    Handles the mapping of converter samples to lane data according to
    JESD204B/C specifications.

    Supported modes (single link):
        L   M   F   S   N'
        1   4   8   1   16
        2   4   4   1   16
        4   4   2   1   16
        8   2   1   2   16
        8   4   1   1   16
    """

    SUPPORTED_MODES = [
        {'L': 1, 'M': 4, 'F': 8, 'S': 1, 'NP': 16},
        {'L': 2, 'M': 4, 'F': 4, 'S': 1, 'NP': 16},
        {'L': 4, 'M': 4, 'F': 2, 'S': 1, 'NP': 16},
        {'L': 8, 'M': 2, 'F': 1, 'S': 2, 'NP': 16},
        {'L': 8, 'M': 4, 'F': 1, 'S': 1, 'NP': 16},
    ]

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.input_buffer = deque()
        self.output_cycle_cnt = 0
        self._validate_mode()

    def _validate_mode(self) -> None:
        """Validate that the configured JESD mode is supported."""
        mode = {
            'L': self.config.jesd_l,
            'M': self.config.jesd_m,
            'F': self.config.jesd_f,
            'S': self.config.jesd_s,
            'NP': self.config.jesd_np
        }

        for supported in self.SUPPORTED_MODES:
            if all(mode.get(k) == v for k, v in supported.items()):
                logger.info(f"Using JESD mode: L={mode['L']}, M={mode['M']}, "
                           f"F={mode['F']}, S={mode['S']}, NP={mode['NP']}")
                return

        logger.warning(f"JESD mode L={mode['L']}, M={mode['M']}, F={mode['F']}, "
                      f"S={mode['S']}, NP={mode['NP']} may not be fully supported")

    @property
    def output_cycles(self) -> int:
        """Number of output cycles per input frame."""
        L, M, F, NP = self.config.jesd_l, self.config.jesd_m, self.config.jesd_f, self.config.jesd_np

        # Based on casex in jtx_transport_single_link.sv
        if L == 1 and M == 4 and F == 8 and NP == 16:
            return 16
        elif L == 2 and M == 4 and F == 4 and NP == 16:
            return 8
        elif L == 4 and M == 4 and F == 2 and NP == 16:
            return 4
        elif L == 8 and M == 2 and F == 1 and NP == 16:
            return 1
        elif L == 8 and M == 4 and F == 1 and NP == 16:
            return 2
        else:
            return 1

    def reset(self) -> None:
        """Reset internal state."""
        self.input_buffer.clear()
        self.output_cycle_cnt = 0

    def input_frame(self, data: np.ndarray) -> None:
        """
        Input a frame of converter data.

        Args:
            data: Array of shape (num_conv, num_samples)
        """
        self.input_buffer.append(data.copy())

    def get_lane_data(self) -> Optional[np.ndarray]:
        """
        Get lane data output.

        Returns:
            Array of shape (num_lanes, octets_per_lane) or None if no data
        """
        if not self.input_buffer:
            return None

        # Simplified transport layer - just return the data in lane format
        # Real implementation would do proper nibble-swapping per JESD204 spec
        frame = self.input_buffer[0]

        L = self.config.jesd_l
        octets_per_lane = 8  # Fixed for this implementation

        lane_data = np.zeros((L, octets_per_lane), dtype=np.uint8)

        # Map samples to lanes (simplified)
        samples_flat = frame.flatten()
        byte_idx = 0

        for sample in samples_flat:
            if byte_idx >= L * octets_per_lane:
                break
            lane_idx = byte_idx % L
            octet_idx = byte_idx // L
            if octet_idx < octets_per_lane:
                # Split 16-bit sample into bytes
                lane_data[lane_idx, octet_idx] = (sample >> 8) & 0xFF
                if octet_idx + 1 < octets_per_lane:
                    lane_data[lane_idx, octet_idx + 1] = sample & 0xFF
            byte_idx += 2

        self.output_cycle_cnt += 1
        if self.output_cycle_cnt >= self.output_cycles:
            self.output_cycle_cnt = 0
            if self.input_buffer:
                self.input_buffer.popleft()

        return lane_data


class TxFSRC:
    """
    Top-level TX FSRC simulation.

    Models: tx_fsrc.sv

    Orchestrates the complete FSRC datapath including:
    - Sample enable generation
    - Hole insertion
    - Optional JESD transport layer
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.sample_en_gen = SampleEnableGenerator(config)
        self.hole_inserter = HoleInserter(config)
        self.jesd_transport = JESDTransportLayer(config)

        # Control signals
        self.fsrc_en = False
        self.fsrc_data_en = False
        self.reset_state = True

        # Statistics
        self.stats = {
            'input_samples': 0,
            'output_samples': 0,
            'holes_inserted': 0,
            'valid_samples_output': 0
        }

    def reset(self) -> None:
        """Reset the FSRC to initial state."""
        self.reset_state = True
        self.fsrc_en = False
        self.fsrc_data_en = False
        self.hole_inserter.reset()
        self.jesd_transport.reset()
        self.stats = {k: 0 for k in self.stats}

    def configure(self, ratio_n: int, ratio_m: int) -> None:
        """
        Configure the FSRC with a new N/M ratio.

        Args:
            ratio_n: Numerator (output rate)
            ratio_m: Denominator (input rate)
        """
        self.config.channel_to_sample_rate_ratio = ratio_n / ratio_m
        self.sample_en_gen = SampleEnableGenerator(self.config)
        logger.info(f"Configured FSRC with ratio {ratio_n}/{ratio_m} = {self.config.channel_to_sample_rate_ratio:.6f}")

    def start(self) -> None:
        """Start the FSRC operation."""
        self.reset_state = False
        self.fsrc_en = True
        self.sample_en_gen.set_accumulators()

    def enable_data(self) -> None:
        """Enable data flow through FSRC."""
        self.fsrc_data_en = True

    def step(self, input_data: np.ndarray) -> Tuple[Optional[np.ndarray], np.ndarray]:
        """
        Process one clock cycle of the FSRC.

        Args:
            input_data: Array of shape (num_conv, num_samples)

        Returns:
            Tuple of (output_data, sample_enables)
            output_data is None if not ready, otherwise shape (num_conv, num_samples)
        """
        if self.reset_state:
            return None, np.zeros(self.config.num_samples, dtype=bool)

        # Generate sample enables
        accum_en = self.fsrc_en and self.fsrc_data_en
        sample_en = self.sample_en_gen.step(accum_en)

        # Track statistics
        self.stats['input_samples'] += input_data.shape[1] * self.config.jesd_m

        if self.fsrc_en:
            # Input samples to buffer
            self.hole_inserter.input_samples(input_data, valid=True)

            # Generate holes (inverted sample_en when fsrc_data_en)
            holes = ~sample_en if self.fsrc_data_en else np.ones(self.config.num_samples, dtype=bool)

            # Try to output
            output_data = self.hole_inserter.output_samples(holes)

            if output_data is not None:
                # Count statistics
                for conv_idx in range(self.config.jesd_m):
                    for sample in output_data[conv_idx]:
                        self.stats['output_samples'] += 1
                        if sample == self.config.fsrc_invalid_sample:
                            self.stats['holes_inserted'] += 1
                        else:
                            self.stats['valid_samples_output'] += 1

            return output_data, sample_en
        else:
            # Bypass mode - pass through directly
            return input_data, np.ones(self.config.num_samples, dtype=bool)


class TxFSRCTestbench:
    """
    Testbench for TX FSRC simulation.

    Models: tb_tx_fsrc.sv

    Provides test infrastructure including:
    - Input data generation
    - Output verification
    - Statistics collection
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.fsrc = TxFSRC(config)
        self.input_queues = [deque() for _ in range(config.max_conv)]
        self.output_count = 0
        self.error_count = 0
        self.cycle_count = 0

    def generate_input_data(self) -> np.ndarray:
        """Generate test input data."""
        data = np.zeros((self.config.max_conv, self.config.num_samples), dtype=np.uint64)

        for conv_idx in range(self.config.jesd_m):
            for sample_idx in range(self.config.num_samples):
                if self.config.random_data:
                    sample = np.random.randint(0, 2**self.config.np_bits)
                elif self.config.identical_data:
                    sample = self.cycle_count % (2**self.config.np_bits)
                else:
                    sample = (self.cycle_count + sample_idx) % (2**self.config.np_bits)

                # Avoid the invalid sample marker
                if sample == self.config.fsrc_invalid_sample:
                    sample ^= 1

                data[conv_idx, sample_idx] = sample
                self.input_queues[conv_idx].append(sample)

        return data

    def verify_output(self, output_data: np.ndarray) -> int:
        """
        Verify output data against expected values.

        Returns:
            Number of errors found
        """
        errors = 0

        for conv_idx in range(self.config.jesd_m):
            for sample_idx in range(self.config.num_samples):
                out_sample = output_data[conv_idx, sample_idx]

                if out_sample != self.config.fsrc_invalid_sample:
                    if self.input_queues[conv_idx]:
                        expected = self.input_queues[conv_idx].popleft()
                        if out_sample != expected:
                            logger.error(f"Data mismatch at conv={conv_idx}, sample={sample_idx}: "
                                       f"expected 0x{expected:04X}, got 0x{out_sample:04X}")
                            errors += 1
                    else:
                        logger.error(f"Output sample with no corresponding input at conv={conv_idx}")
                        errors += 1

        return errors

    def run(self, num_cycles: int, ratio_changes: Optional[List[Tuple[int, int, int]]] = None) -> Dict[str, Any]:
        """
        Run the testbench simulation.

        Args:
            num_cycles: Number of clock cycles to simulate
            ratio_changes: Optional list of (cycle, ratio_n, ratio_m) tuples
                          to change the FSRC ratio during simulation

        Returns:
            Dictionary of simulation results
        """
        ratio_changes = ratio_changes or []
        ratio_change_idx = 0

        # Initialize
        self.fsrc.reset()
        logger.info("Starting TX FSRC simulation...")

        # Start sequence (mimics tb_tx_fsrc.sv startup)
        self.fsrc.start()
        self.fsrc.enable_data()

        results = {
            'input_samples': [],
            'output_samples': [],
            'sample_enables': [],
            'errors': 0
        }

        for cycle in range(num_cycles):
            self.cycle_count = cycle

            # Check for ratio change
            while (ratio_change_idx < len(ratio_changes) and
                   ratio_changes[ratio_change_idx][0] <= cycle):
                _, n, m = ratio_changes[ratio_change_idx]
                logger.info(f"Cycle {cycle}: Changing ratio to {n}/{m}")
                self.fsrc.configure(n, m)
                self.fsrc.sample_en_gen.set_accumulators()
                ratio_change_idx += 1

            # Generate input
            input_data = self.generate_input_data()
            results['input_samples'].append(input_data.copy())

            # Process
            output_data, sample_en = self.fsrc.step(input_data)
            results['sample_enables'].append(sample_en.copy())

            if output_data is not None:
                results['output_samples'].append(output_data.copy())
                errors = self.verify_output(output_data)
                results['errors'] += errors
                self.error_count += errors
                self.output_count += 1

        # Add statistics
        results['stats'] = self.fsrc.stats.copy()
        results['total_cycles'] = num_cycles
        results['output_cycles'] = self.output_count
        results['total_errors'] = self.error_count

        return results


def run_basic_test() -> None:
    """Run a basic FSRC test with default parameters."""
    config = FSRCConfig(
        np_bits=16,
        data_width=256,
        max_conv=4,
        jesd_l=8,
        jesd_m=2,
        jesd_f=1,
        jesd_s=2,
        jesd_np=16,
        channel_to_sample_rate_ratio=2/3,  # 2:3 ratio
    )

    tb = TxFSRCTestbench(config)
    results = tb.run(num_cycles=100)

    print("\n" + "="*60)
    print("Basic Test Results")
    print("="*60)
    print(f"Total cycles: {results['total_cycles']}")
    print(f"Output cycles: {results['output_cycles']}")
    print(f"Total errors: {results['total_errors']}")
    print(f"Statistics: {results['stats']}")

    # Calculate actual ratio
    if results['stats']['output_samples'] > 0:
        actual_ratio = results['stats']['valid_samples_output'] / results['stats']['output_samples']
        print(f"Actual valid/total ratio: {actual_ratio:.4f}")
        print(f"Expected ratio: {config.channel_to_sample_rate_ratio:.4f}")


def run_ratio_change_test() -> None:
    """Run a test with changing N/M ratios."""
    config = FSRCConfig(
        np_bits=16,
        data_width=256,
        max_conv=4,
        jesd_l=8,
        jesd_m=2,
        jesd_f=1,
        jesd_s=2,
        jesd_np=16,
        channel_to_sample_rate_ratio=1/2,
    )

    # Schedule ratio changes
    ratio_changes = [
        (0, 1, 2),    # Start with 1:2 ratio
        (50, 2, 3),   # Change to 2:3 at cycle 50
        (100, 3, 4),  # Change to 3:4 at cycle 100
        (150, 4, 5),  # Change to 4:5 at cycle 150
        (200, 5, 6),  # Change to 5:6 at cycle 200
    ]

    tb = TxFSRCTestbench(config)
    results = tb.run(num_cycles=250, ratio_changes=ratio_changes)

    print("\n" + "="*60)
    print("Ratio Change Test Results")
    print("="*60)
    print(f"Total cycles: {results['total_cycles']}")
    print(f"Output cycles: {results['output_cycles']}")
    print(f"Total errors: {results['total_errors']}")
    print(f"Statistics: {results['stats']}")


def run_jesd_mode_sweep() -> None:
    """Run tests across different JESD modes."""
    modes = [
        {'L': 1, 'M': 4, 'F': 8, 'S': 1, 'NP': 16},
        {'L': 2, 'M': 4, 'F': 4, 'S': 1, 'NP': 16},
        {'L': 4, 'M': 4, 'F': 2, 'S': 1, 'NP': 16},
        {'L': 8, 'M': 2, 'F': 1, 'S': 2, 'NP': 16},
        {'L': 8, 'M': 4, 'F': 1, 'S': 1, 'NP': 16},
    ]

    print("\n" + "="*60)
    print("JESD Mode Sweep Test")
    print("="*60)

    for mode in modes:
        config = FSRCConfig(
            np_bits=16,
            data_width=256,
            max_conv=4,
            jesd_l=mode['L'],
            jesd_m=mode['M'],
            jesd_f=mode['F'],
            jesd_s=mode['S'],
            jesd_np=mode['NP'],
            channel_to_sample_rate_ratio=2/3,
        )

        tb = TxFSRCTestbench(config)
        results = tb.run(num_cycles=50)

        print(f"\nMode L={mode['L']}, M={mode['M']}, F={mode['F']}, S={mode['S']}, NP={mode['NP']}:")
        print(f"  Errors: {results['total_errors']}")
        print(f"  Valid samples: {results['stats']['valid_samples_output']}")
        print(f"  Holes inserted: {results['stats']['holes_inserted']}")


def visualize_sample_pattern(config: FSRCConfig, num_cycles: int = 20) -> None:
    """Visualize the sample enable pattern over several cycles."""
    fsrc = TxFSRC(config)
    fsrc.start()
    fsrc.enable_data()

    print("\n" + "="*60)
    print(f"Sample Enable Pattern (ratio = {config.channel_to_sample_rate_ratio:.4f})")
    print("="*60)
    print("Legend: # = valid sample, . = hole")
    print()

    for cycle in range(num_cycles):
        input_data = np.zeros((config.max_conv, config.num_samples), dtype=np.uint64)
        _, sample_en = fsrc.step(input_data)

        pattern = ''.join(['#' if en else '.' for en in sample_en])
        valid_count = np.sum(sample_en)
        print(f"Cycle {cycle:3d}: [{pattern}] ({valid_count}/{config.num_samples} valid)")


def run_comprehensive_simulation():
    """Run a comprehensive simulation with all features."""
    print("="*60)
    print("TX FSRC Comprehensive Python Simulation")
    print("Based on: tb_tx_fsrc.sv")
    print("="*60)

    # Basic test
    run_basic_test()

    # Ratio change test
    run_ratio_change_test()

    # JESD mode sweep
    run_jesd_mode_sweep()

    # Visualize pattern
    config = FSRCConfig(
        np_bits=16,
        data_width=256,
        max_conv=4,
        jesd_l=8,
        jesd_m=2,
        jesd_f=1,
        jesd_s=2,
        channel_to_sample_rate_ratio=2/3,
    )
    visualize_sample_pattern(config)

    print("\n" + "="*60)
    print("Simulation Complete")
    print("="*60)


if __name__ == "__main__":
    run_comprehensive_simulation()
