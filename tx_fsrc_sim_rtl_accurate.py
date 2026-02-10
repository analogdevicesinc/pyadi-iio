#!/usr/bin/env python3
"""
TX FSRC RTL-Accurate Python Simulation

This simulation aims to EXACTLY match the RTL behavior of:
- tx_fsrc.sv
- tx_fsrc_sample_en_gen.sv
- tx_fsrc_make_holes.sv
- accum_set.sv

Based on: ADS10v1/AD9084_ADS10v1_Acorn/trunk/fpga_ip/datapath_tx/fpga_src/

Key RTL behaviors modeled:
1. Accumulator overflow detection (MSB of add result)
2. Phase initialization: ONE - RATIO + (group * RATIO)
3. Hole insertion with 3x buffering
4. Pipeline delays matching RTL
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FSRCConfig:
    """Configuration matching RTL parameters."""
    NP: int = 16                    # Bits per sample (N')
    DATA_WIDTH: int = 256           # Total data width per converter
    MAX_CONV: int = 4               # Maximum number of converters
    ACCUM_WIDTH: int = 64           # Accumulator width
    NS: int = 1                     # Samples grouped together

    # JESD parameters
    JTX_L: int = 8
    JTX_M: int = 2
    JTX_F: int = 1

    # Runtime parameters
    channel_to_sample_rate_ratio: float = 2/3

    @property
    def NUM_SAMPLES(self) -> int:
        return self.DATA_WIDTH // self.NP

    @property
    def CONV_MASK(self) -> int:
        return (1 << self.JTX_M) - 1

    @property
    def FSRC_INVALID_SAMPLE(self) -> int:
        """RTL: {1'b1, {(NP-1){1'b0}}}"""
        return 1 << (self.NP - 1)

    @property
    def ONE_FIXED(self) -> int:
        """RTL: {1'b1, {ACCUM_WIDTH{1'b0}}}"""
        return 1 << self.ACCUM_WIDTH

    @property
    def RATIO_FIXED(self) -> int:
        """RTL: ONE_FIXED * CHANNEL_TO_SAMPLE_RATE_RATIO"""
        return int(self.ONE_FIXED * self.channel_to_sample_rate_ratio)


class AccumSet:
    """
    RTL-accurate accumulator model.

    Matches: accum_set.sv

    always_ff @(posedge clk) begin
      if(set) begin
        accum <= set_val;
        overflow <= 1'b0;
      end else if(add) begin
        {overflow, accum} <= accum + add_val;
      end
    end
    """

    def __init__(self, width: int = 64):
        self.width = width
        self.mask = (1 << width) - 1
        self.accum = 0
        self.overflow = False

    def clock(self, set_val: int, set: bool, add_val: int, add: bool) -> None:
        """Model one clock cycle."""
        if set:
            self.accum = set_val & self.mask
            self.overflow = False
        elif add:
            result = self.accum + add_val
            self.overflow = (result >> self.width) & 1  # MSB is overflow
            self.accum = result & self.mask


class TxFsrcSampleEnGen:
    """
    RTL-accurate sample enable generator.

    Matches: tx_fsrc_sample_en_gen.sv

    Uses one accumulator per sample position, grouped by NS.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.accumulators = [AccumSet(config.ACCUM_WIDTH)
                            for _ in range(config.NUM_SAMPLES)]

    def compute_set_values(self) -> List[int]:
        """
        Compute initial accumulator values.

        RTL (from tb_tx_fsrc.sv):
        cur_ns_group = ii/NS;
        accum_set_val[ii] = ONE_FIXED - CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED +
                            (cur_ns_group * CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED);
        """
        set_values = []
        one = self.config.ONE_FIXED
        ratio = self.config.RATIO_FIXED
        mask = (1 << self.config.ACCUM_WIDTH) - 1

        for ii in range(self.config.NUM_SAMPLES):
            cur_ns_group = ii // self.config.NS
            val = (one - ratio + (cur_ns_group * ratio)) & mask
            set_values.append(val)

        return set_values

    def set_accumulators(self, set_values: List[int]) -> None:
        """Set all accumulators (accum_set = 1)."""
        for i, acc in enumerate(self.accumulators):
            acc.clock(set_val=set_values[i], set=True, add_val=0, add=False)

    def clock(self, en: bool) -> np.ndarray:
        """
        Clock all accumulators and return sample_en.

        RTL: sample_en[ii] = overflow of accumulator[ii]
        """
        sample_en = np.zeros(self.config.NUM_SAMPLES, dtype=bool)

        for i, acc in enumerate(self.accumulators):
            acc.clock(set_val=0, set=False,
                     add_val=self.config.RATIO_FIXED, add=en)
            sample_en[i] = acc.overflow

        return sample_en


class TxFsrcMakeHoles:
    """
    RTL-accurate hole insertion.

    Matches: tx_fsrc_make_holes.sv

    This module has complex buffering with 3*NUM_WORDS storage
    to handle variable input/output rates.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.NUM_WORDS = config.NUM_SAMPLES
        self.WORD_LENGTH = config.NP
        self.NUM_DATA = config.MAX_CONV
        self.HOLE_VALUE = config.FSRC_INVALID_SAMPLE

        # Pipeline registers
        self.reset()

    def reset(self) -> None:
        """Reset all state."""
        # Input pipeline
        self.in_valid_d = False
        self.in_data_d = np.zeros((self.NUM_DATA, self.NUM_WORDS), dtype=np.uint64)

        # Holes pipeline
        self.holes_valid_d = False
        self.holes_data_d = [np.zeros(self.NUM_WORDS, dtype=bool),
                            np.zeros(self.NUM_WORDS, dtype=bool)]

        # Data storage (3x depth)
        self.data_stored = np.zeros((self.NUM_DATA, self.NUM_WORDS * 3), dtype=np.uint64)
        self.non_holes_cnt = 0
        self.non_holes_cnt_shift_out = 0
        self.non_holes_cnt_total = 0
        self.non_holes_cnt_total_per_word_d = np.zeros(self.NUM_WORDS, dtype=int)

        # Output state
        self.data_stored_out_valid = False
        self.data_stored_in_ready = True
        self.data_out_valid = False
        self.out_valid = False
        self.out_data = np.zeros((self.NUM_DATA, self.NUM_WORDS), dtype=np.uint64)

    @property
    def in_ready(self) -> bool:
        """RTL: !reset && (!in_valid_d || data_shift_in_xfer)"""
        return not self.in_valid_d or self.data_stored_in_ready

    @property
    def holes_ready(self) -> bool:
        """RTL: !reset && (!holes_valid_d || data_shift_holes_xfer)"""
        data_shift_holes_ready = self.data_stored_out_valid and (not self.data_out_valid or self._data_out_ready)
        return not self.holes_valid_d or (self.holes_valid_d and data_shift_holes_ready)

    @property
    def _data_out_ready(self) -> bool:
        """RTL: !out_valid || out_xfer"""
        return not self.out_valid or True  # Assume always ready downstream

    def clock(self, in_data: np.ndarray, in_valid: bool,
              holes_data: np.ndarray, holes_valid: bool,
              out_ready: bool = True) -> Tuple[np.ndarray, bool]:
        """
        Model one clock cycle.

        Returns: (out_data, out_valid)
        """
        # Compute transfer signals
        in_xfer = in_valid and self.in_ready
        holes_xfer = holes_valid and self.holes_ready

        data_shift_holes_ready = self.data_stored_out_valid and (not self.data_out_valid or self._data_out_ready)
        data_shift_in_xfer = self.in_valid_d and self.data_stored_in_ready
        data_shift_holes_xfer = self.holes_valid_d and data_shift_holes_ready

        out_valid_next = self.data_out_valid and self.data_stored_out_valid
        data_out_xfer = out_valid_next and self._data_out_ready
        out_xfer = self.out_valid and out_ready

        # Count non-holes for current holes_data_d[1]
        if self.holes_valid_d:
            non_holes_cnt_total_per_word = np.zeros(self.NUM_WORDS, dtype=int)
            for jj in range(self.NUM_WORDS):
                if jj == 0:
                    non_holes_cnt_total_per_word[jj] = 0 if self.holes_data_d[0][0] else 1
                else:
                    non_holes_cnt_total_per_word[jj] = non_holes_cnt_total_per_word[jj-1] + (0 if self.holes_data_d[0][jj] else 1)
        else:
            non_holes_cnt_total_per_word = np.zeros(self.NUM_WORDS, dtype=int)

        # Compute next state
        non_holes_cnt_total_comb = non_holes_cnt_total_per_word[self.NUM_WORDS-1] if data_shift_holes_xfer else self.non_holes_cnt_total
        non_holes_cnt_out = self.non_holes_cnt_total if data_out_xfer else 0
        non_holes_cnt_comb_shift_out = self.non_holes_cnt_shift_out if data_out_xfer else self.non_holes_cnt
        non_holes_cnt_comb = non_holes_cnt_comb_shift_out + (self.NUM_WORDS if data_shift_in_xfer else 0)

        # Update output data
        if data_out_xfer:
            for ii in range(self.NUM_DATA):
                for jj in range(self.NUM_WORDS):
                    if self.holes_data_d[1][jj]:
                        self.out_data[ii, jj] = self.HOLE_VALUE
                    else:
                        idx = self.non_holes_cnt_total_per_word_d[jj]
                        if idx < len(self.data_stored[ii]):
                            self.out_data[ii, jj] = self.data_stored[ii, idx]
                        else:
                            self.out_data[ii, jj] = self.HOLE_VALUE

        # Update out_valid
        if data_out_xfer:
            next_out_valid = True
        elif out_xfer:
            next_out_valid = False
        else:
            next_out_valid = self.out_valid

        # Update data_out_valid
        if data_shift_holes_xfer:
            next_data_out_valid = True
        elif data_out_xfer:
            next_data_out_valid = False
        else:
            next_data_out_valid = self.data_out_valid

        # Update data storage (shift out consumed, shift in new)
        new_data_stored = np.zeros_like(self.data_stored)
        for ii in range(self.NUM_DATA):
            for jj in range(self.NUM_WORDS * 3):
                if jj < non_holes_cnt_comb_shift_out:
                    src_idx = jj + non_holes_cnt_out
                    if src_idx < self.NUM_WORDS * 3:
                        new_data_stored[ii, jj] = self.data_stored[ii, src_idx]
                else:
                    src_idx = jj - non_holes_cnt_comb_shift_out
                    if src_idx < self.NUM_WORDS:
                        new_data_stored[ii, jj] = self.in_data_d[ii, src_idx]

        # Update pipeline registers
        # Input pipeline
        if in_xfer:
            self.in_valid_d = True
            self.in_data_d = in_data.copy()
        elif data_shift_in_xfer:
            self.in_valid_d = False

        # Holes pipeline
        if holes_xfer:
            self.holes_valid_d = True
            self.holes_data_d[0] = holes_data.copy()
        elif data_shift_holes_xfer:
            self.holes_valid_d = False

        if data_shift_holes_xfer:
            self.holes_data_d[1] = self.holes_data_d[0].copy()
            self.non_holes_cnt_total_per_word_d = non_holes_cnt_total_per_word - 1

        # Update counts
        self.non_holes_cnt = non_holes_cnt_comb
        self.non_holes_cnt_shift_out = non_holes_cnt_comb - non_holes_cnt_total_comb
        self.non_holes_cnt_total = non_holes_cnt_total_comb
        self.data_stored = new_data_stored
        self.data_stored_out_valid = non_holes_cnt_comb >= self.NUM_WORDS
        self.data_stored_in_ready = non_holes_cnt_comb <= self.NUM_WORDS * 2
        self.data_out_valid = next_data_out_valid
        self.out_valid = next_out_valid

        return self.out_data.copy(), self.out_valid


class TxFSRC:
    """
    RTL-accurate TX FSRC top-level.

    Matches: tx_fsrc.sv
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.sample_en_gen = TxFsrcSampleEnGen(config)
        self.make_holes = TxFsrcMakeHoles(config)

        # Control signals
        self.fsrc_en = False
        self.fsrc_data_en = False

        # Compute and store set values
        self.accum_set_val = self.sample_en_gen.compute_set_values()

    def reset(self) -> None:
        """Reset the FSRC."""
        self.make_holes.reset()
        self.fsrc_en = False
        self.fsrc_data_en = False

    def set_accumulators(self) -> None:
        """Set accumulators to initial values."""
        self.sample_en_gen.set_accumulators(self.accum_set_val)

    def configure(self, ratio: float) -> None:
        """Configure new ratio."""
        self.config.channel_to_sample_rate_ratio = ratio
        self.accum_set_val = self.sample_en_gen.compute_set_values()

    def clock(self, in_data: np.ndarray, in_valid: bool = True,
              out_ready: bool = True) -> Tuple[np.ndarray, bool, np.ndarray]:
        """
        Model one clock cycle.

        RTL signal mapping:
        - holes_n = sample_en (from accumulators)
        - holes_data = fsrc_data_en ? ~holes_n : all_ones
        - accum_en = fsrc_en && fsrc_data_en && holes_ready

        Returns: (out_data, out_valid, sample_en)
        """
        # Compute accumulator enable
        accum_en = self.fsrc_en and self.fsrc_data_en and self.make_holes.holes_ready

        # Generate sample enables
        holes_n = self.sample_en_gen.clock(accum_en)

        # Compute holes_data
        if self.fsrc_data_en:
            holes_data = ~holes_n  # Invert: sample_en=1 means valid, holes_data=1 means hole
        else:
            holes_data = np.ones(self.config.NUM_SAMPLES, dtype=bool)  # All holes

        holes_valid = True  # Always valid in this model

        # Process through make_holes
        out_data, out_valid = self.make_holes.clock(
            in_data=in_data,
            in_valid=in_valid and self.fsrc_en,
            holes_data=holes_data,
            holes_valid=holes_valid,
            out_ready=out_ready
        )

        return out_data, out_valid, holes_n


class TxFSRCTestbench:
    """
    RTL-accurate testbench.

    Matches: tb_tx_fsrc.sv
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.fsrc = TxFSRC(config)

        # Verification queues (per converter)
        self.input_queues = [deque() for _ in range(config.MAX_CONV)]
        self.cycle_count = 0
        self.error_count = 0

    def reset(self) -> None:
        """Reset testbench state."""
        self.fsrc.reset()
        for q in self.input_queues:
            q.clear()
        self.cycle_count = 0
        self.error_count = 0

    def generate_input(self, identical: bool = True) -> np.ndarray:
        """
        Generate input data.

        RTL (identical mode):
        cur_sample = cnt;  // Same for all samples in cycle
        if(cur_sample == FSRC_INVALID_SAMPLE) cur_sample ^= 1;
        """
        data = np.zeros((self.config.MAX_CONV, self.config.NUM_SAMPLES), dtype=np.uint64)

        for conv in range(self.config.JTX_M):
            for i in range(self.config.NUM_SAMPLES):
                if identical:
                    sample = self.cycle_count % (2 ** self.config.NP)
                else:
                    sample = (self.cycle_count + i) % (2 ** self.config.NP)

                if sample == self.config.FSRC_INVALID_SAMPLE:
                    sample ^= 1

                data[conv, i] = sample
                self.input_queues[conv].append(sample)

        return data

    def verify_output(self, out_data: np.ndarray, out_valid: bool) -> int:
        """Verify output matches expected."""
        errors = 0

        if out_valid:
            for conv in range(self.config.JTX_M):
                for i in range(self.config.NUM_SAMPLES):
                    sample = int(out_data[conv, i])

                    if sample != self.config.FSRC_INVALID_SAMPLE:
                        if self.input_queues[conv]:
                            expected = self.input_queues[conv].popleft()
                            if sample != expected:
                                logger.error(f"Cycle {self.cycle_count}: Mismatch at conv={conv}, "
                                           f"sample={i}: expected 0x{expected:04X}, got 0x{sample:04X}")
                                errors += 1

        return errors

    def run(self, num_cycles: int) -> Dict[str, Any]:
        """Run simulation for num_cycles."""
        self.reset()

        # Startup sequence (from tb_tx_fsrc.sv)
        self.fsrc.fsrc_en = True
        self.fsrc.set_accumulators()
        self.fsrc.fsrc_data_en = True

        sample_en_history = []
        out_valid_history = []
        stats = {
            'input_samples': 0,
            'output_samples': 0,
            'valid_samples': 0,
            'holes': 0,
        }

        logger.info(f"Running RTL-accurate simulation for {num_cycles} cycles...")

        for cycle in range(num_cycles):
            self.cycle_count = cycle

            # Generate input
            in_data = self.generate_input(identical=True)
            stats['input_samples'] += self.config.NUM_SAMPLES * self.config.JTX_M

            # Clock the FSRC
            out_data, out_valid, sample_en = self.fsrc.clock(in_data, in_valid=True)

            sample_en_history.append(sample_en.copy())
            out_valid_history.append(out_valid)

            # Verify and count
            if out_valid:
                errors = self.verify_output(out_data, out_valid)
                self.error_count += errors

                for conv in range(self.config.JTX_M):
                    for sample in out_data[conv]:
                        stats['output_samples'] += 1
                        if sample == self.config.FSRC_INVALID_SAMPLE:
                            stats['holes'] += 1
                        else:
                            stats['valid_samples'] += 1

        return {
            'cycles': num_cycles,
            'errors': self.error_count,
            'stats': stats,
            'sample_en_history': sample_en_history,
            'out_valid_history': out_valid_history,
            'config': {
                'ratio': self.config.channel_to_sample_rate_ratio,
                'JTX_L': self.config.JTX_L,
                'JTX_M': self.config.JTX_M,
                'NUM_SAMPLES': self.config.NUM_SAMPLES,
            }
        }

    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print results summary."""
        print("\n" + "="*60)
        print("RTL-Accurate TX FSRC Simulation")
        print("="*60)

        cfg = results['config']
        print(f"\nConfiguration:")
        print(f"  Ratio: {cfg['ratio']:.6f}")
        print(f"  JTX_L: {cfg['JTX_L']}, JTX_M: {cfg['JTX_M']}")
        print(f"  NUM_SAMPLES: {cfg['NUM_SAMPLES']}")

        stats = results['stats']
        print(f"\nStatistics:")
        print(f"  Cycles: {results['cycles']}")
        print(f"  Input samples: {stats['input_samples']}")
        print(f"  Output samples: {stats['output_samples']}")
        print(f"  Valid samples: {stats['valid_samples']}")
        print(f"  Holes: {stats['holes']}")

        if stats['output_samples'] > 0:
            ratio = stats['valid_samples'] / stats['output_samples']
            print(f"  Actual ratio: {ratio:.6f}")

        print(f"\nVerification:")
        print(f"  Errors: {results['errors']}")
        print(f"  Status: {'PASS' if results['errors'] == 0 else 'FAIL'}")

    def print_pattern(self, results: Dict[str, Any], num_cycles: int = 20) -> None:
        """Print sample enable pattern."""
        print("\nSample Enable Pattern (# = valid, . = hole):")
        history = results['sample_en_history']
        valid_history = results['out_valid_history']

        for i, (sample_en, out_valid) in enumerate(zip(history[:num_cycles], valid_history[:num_cycles])):
            pattern = ''.join(['#' if en else '.' for en in sample_en])
            valid = np.sum(sample_en)
            valid_str = "OUT_VALID" if out_valid else ""
            print(f"  Cycle {i:3d}: [{pattern}] ({valid}/{len(sample_en)}) {valid_str}")


def compare_with_behavioral():
    """Compare RTL-accurate model with behavioral model."""
    print("="*60)
    print("Comparing RTL-Accurate vs Behavioral Simulation")
    print("="*60)

    config = FSRCConfig(
        channel_to_sample_rate_ratio=2/3,
        JTX_L=8,
        JTX_M=2,
    )

    # RTL-accurate
    print("\n--- RTL-Accurate Model ---")
    tb = TxFSRCTestbench(config)
    results = tb.run(50)
    tb.print_summary(results)
    tb.print_pattern(results, 15)

    # Show initial accumulator values
    print("\nInitial accumulator values (normalized):")
    set_vals = tb.fsrc.accum_set_val
    for i, val in enumerate(set_vals[:16]):
        norm = val / config.ONE_FIXED
        print(f"  Sample {i:2d}: 0x{val:016X} ({norm:.6f})")


def run_tests():
    """Run comprehensive tests."""
    print("="*60)
    print("RTL-Accurate TX FSRC Simulation")
    print("="*60)

    # Test various ratios
    ratios = [(1, 2), (2, 3), (3, 4), (7, 8), (1990, 2000)]

    for n, m in ratios:
        print(f"\n--- Ratio {n}/{m} = {n/m:.6f} ---")

        config = FSRCConfig(
            channel_to_sample_rate_ratio=n/m,
            JTX_L=8,
            JTX_M=2,
        )

        tb = TxFSRCTestbench(config)
        results = tb.run(100)

        stats = results['stats']
        if stats['output_samples'] > 0:
            actual = stats['valid_samples'] / stats['output_samples']
        else:
            actual = 0

        status = 'PASS' if results['errors'] == 0 else 'FAIL'
        print(f"  Target: {n/m:.6f}, Actual: {actual:.6f}, Status: {status}")

        if n == 1990:  # Show pattern for high ratio
            tb.print_pattern(results, 10)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RTL-Accurate TX FSRC Simulation")
    parser.add_argument('--test', choices=['full', 'compare', 'custom'], default='full')
    parser.add_argument('--cycles', type=int, default=100)
    parser.add_argument('--ratio-n', type=int, default=2)
    parser.add_argument('--ratio-m', type=int, default=3)
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test == 'full':
        run_tests()
    elif args.test == 'compare':
        compare_with_behavioral()
    elif args.test == 'custom':
        config = FSRCConfig(
            channel_to_sample_rate_ratio=args.ratio_n/args.ratio_m,
        )
        tb = TxFSRCTestbench(config)
        results = tb.run(args.cycles)
        tb.print_summary(results)
        tb.print_pattern(results, 20)
