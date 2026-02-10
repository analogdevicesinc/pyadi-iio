#!/usr/bin/env python3
"""
TX FSRC Simulation - RTL Phase Matching

This simulation focuses on EXACTLY matching the RTL accumulator behavior,
which is the core of the FSRC algorithm. The hole insertion buffering is
simplified but the sample enable pattern should match the RTL exactly.

Key RTL behaviors matched:
1. Accumulator formula: ONE - RATIO + (ns_group * RATIO)
2. Overflow detection on MSB
3. Sample enable = accumulator overflow

The complex buffering in tx_fsrc_make_holes.sv is simplified because:
- It introduces variable latency based on data flow
- The core algorithm (which samples are valid/holes) is determined by accumulators
- Buffering only affects timing, not which samples become holes
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class RTLConfig:
    """Configuration exactly matching RTL parameters from tb_tx_fsrc.sv"""
    # From tb_tx_fsrc.sv localparams
    JTX_L: int = 8
    JTX_M: int = 2
    JTX_F: int = 1
    NP: int = 16
    DATA_WIDTH: int = 256
    MAX_CONV: int = 4
    ACCUM_WIDTH: int = 64
    NS: int = 1  # Number of samples grouped together

    # Runtime parameter
    CHANNEL_TO_SAMPLE_RATE_RATIO: float = 2/3

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
    def CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED(self) -> int:
        """RTL: ONE_FIXED * CHANNEL_TO_SAMPLE_RATE_RATIO"""
        return int(self.ONE_FIXED * self.CHANNEL_TO_SAMPLE_RATE_RATIO)


def compute_accum_set_values(config: RTLConfig) -> List[int]:
    """
    Compute initial accumulator values EXACTLY as in tb_tx_fsrc.sv.

    RTL code:
    ```systemverilog
    for(ii = 0; ii < NUM_SAMPLES; ii=ii+1) begin
      cur_ns_group = ii/NS;
      accum_set_val[ii] = ONE_FIXED - CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED +
                          (cur_ns_group * CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED);
    end
    ```
    """
    values = []
    ONE = config.ONE_FIXED
    RATIO = config.CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED
    MASK = (1 << config.ACCUM_WIDTH) - 1

    for ii in range(config.NUM_SAMPLES):
        cur_ns_group = ii // config.NS
        val = (ONE - RATIO + (cur_ns_group * RATIO)) & MASK
        values.append(val)

    return values


class RTLAccumulator:
    """
    Exact model of accum_set.sv

    ```systemverilog
    always_ff @(posedge clk) begin
      if(set) begin
        accum <= set_val;
        overflow <= 1'b0;
      end else if(add) begin
        {overflow, accum} <= accum + add_val;
      end
    end
    ```
    """
    def __init__(self, width: int):
        self.width = width
        self.mask = (1 << width) - 1
        self.accum = 0
        self.overflow = False

    def clock(self, set: bool, set_val: int, add: bool, add_val: int) -> bool:
        """Execute one clock cycle, return overflow."""
        if set:
            self.accum = set_val & self.mask
            self.overflow = False
        elif add:
            result = self.accum + add_val
            # {overflow, accum} <= accum + add_val
            # overflow is the bit above the mask
            self.overflow = bool((result >> self.width) & 1)
            self.accum = result & self.mask

        return self.overflow


class RTLSampleEnableGenerator:
    """
    Exact model of tx_fsrc_sample_en_gen.sv

    ```systemverilog
    for(ii=0; ii<NUM_SAMPLES; ii=ii+1) begin : accum_gen
      accum_set #(.WIDTH(ACCUM_WIDTH)) accum_set (
        .clk(clk),
        .set_val(set_val[ii]),
        .set(set),
        .add_val(add_val),
        .add(en),
        .accum(),
        .overflow(sample_en[ii])
      );
    end
    ```
    """
    def __init__(self, config: RTLConfig):
        self.config = config
        self.accumulators = [RTLAccumulator(config.ACCUM_WIDTH)
                            for _ in range(config.NUM_SAMPLES)]

    def set_all(self, set_values: List[int]) -> None:
        """Set all accumulators to initial values."""
        for i, acc in enumerate(self.accumulators):
            acc.clock(set=True, set_val=set_values[i], add=False, add_val=0)

    def clock(self, en: bool, add_val: int) -> np.ndarray:
        """
        Clock all accumulators.

        Returns sample_en where sample_en[i] = overflow of accumulator[i]
        """
        sample_en = np.zeros(self.config.NUM_SAMPLES, dtype=bool)

        for i, acc in enumerate(self.accumulators):
            overflow = acc.clock(set=False, set_val=0, add=en, add_val=add_val)
            sample_en[i] = overflow

        return sample_en


class RTLMatchingSimulation:
    """
    Simulation that exactly matches RTL accumulator behavior.

    The hole insertion is simplified but sample_en pattern matches RTL.
    """
    def __init__(self, config: RTLConfig):
        self.config = config
        self.sample_en_gen = RTLSampleEnableGenerator(config)
        self.accum_set_values = compute_accum_set_values(config)

        # State
        self.fsrc_en = False
        self.fsrc_data_en = False
        self.holes_ready = True  # Simplified: always ready

        # Data queue for verification
        self.input_queue = deque()

    def reset(self) -> None:
        """Reset state."""
        self.input_queue.clear()
        self.fsrc_en = False
        self.fsrc_data_en = False

    def set_accumulators(self) -> None:
        """Set accumulators to initial values (accum_set pulse)."""
        self.sample_en_gen.set_all(self.accum_set_values)

    def clock(self, in_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute one clock cycle.

        RTL signal mapping:
        - accum_en = fsrc_en && fsrc_data_en && holes_ready
        - holes_n = sample_en (accumulator overflows)
        - holes_data = fsrc_data_en ? ~holes_n : '1

        Returns: (output_data, sample_en)
        """
        # Accumulator enable logic from tx_fsrc.sv:
        # assign accum_en = !reset && fsrc_en && fsrc_data_en && holes_ready;
        accum_en = self.fsrc_en and self.fsrc_data_en and self.holes_ready

        # Sample enable from accumulators
        sample_en = self.sample_en_gen.clock(
            en=accum_en,
            add_val=self.config.CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED
        )

        # Holes logic from tx_fsrc.sv:
        # assign holes_data = fsrc_data_en ? {MAX_CONV{~holes_n}} : '1;
        if self.fsrc_data_en:
            holes = ~sample_en  # Invert: sample_en=True means valid (not a hole)
        else:
            holes = np.ones(self.config.NUM_SAMPLES, dtype=bool)

        # Generate output with holes (simplified - no buffering delay)
        output = np.zeros((self.config.MAX_CONV, self.config.NUM_SAMPLES), dtype=np.uint64)

        for conv in range(self.config.JTX_M):
            for i in range(self.config.NUM_SAMPLES):
                if holes[i]:
                    output[conv, i] = self.config.FSRC_INVALID_SAMPLE
                else:
                    # Get sample from input
                    output[conv, i] = in_data[conv, i]

        return output, sample_en


def run_rtl_pattern_test():
    """Test that sample_en pattern matches RTL."""
    print("="*70)
    print("RTL Phase/Pattern Matching Test")
    print("="*70)

    ratios = [
        (2, 3, "Standard ratio"),
        (1, 2, "50% ratio"),
        (3, 4, "75% ratio"),
        (1990, 2000, "High ratio (99.5%)"),
    ]

    for n, m, desc in ratios:
        print(f"\n--- Ratio {n}/{m} ({desc}) ---")

        config = RTLConfig(CHANNEL_TO_SAMPLE_RATE_RATIO=n/m)
        sim = RTLMatchingSimulation(config)

        # Print initial accumulator values
        print(f"\nInitial accumulator values (RTL formula):")
        print(f"  ONE_FIXED = 0x{config.ONE_FIXED:X}")
        print(f"  RATIO_FIXED = 0x{config.CHANNEL_TO_SAMPLE_RATE_RATIO_FIXED:X}")

        for i in range(min(4, config.NUM_SAMPLES)):
            val = sim.accum_set_values[i]
            norm = val / config.ONE_FIXED
            print(f"  accum_set_val[{i}] = 0x{val:016X} ({norm:.6f})")

        print(f"  ... ({config.NUM_SAMPLES - 4} more)")

        # Run simulation
        sim.fsrc_en = True
        sim.set_accumulators()
        sim.fsrc_data_en = True

        print(f"\nSample enable pattern (first 15 cycles):")
        print("  (# = valid/overflow, . = hole/no overflow)")

        for cycle in range(15):
            in_data = np.zeros((config.MAX_CONV, config.NUM_SAMPLES), dtype=np.uint64)
            _, sample_en = sim.clock(in_data)

            pattern = ''.join(['#' if en else '.' for en in sample_en])
            valid_count = np.sum(sample_en)
            print(f"  Cycle {cycle:2d}: [{pattern}] ({valid_count}/{config.NUM_SAMPLES})")


def analyze_phase_distribution():
    """Analyze phase distribution for RTL formula."""
    print("\n" + "="*70)
    print("RTL Phase Distribution Analysis")
    print("="*70)

    ratios = [(2, 3), (1990, 2000)]

    for n, m in ratios:
        print(f"\n--- Ratio {n}/{m} = {n/m:.6f} ---")

        config = RTLConfig(CHANNEL_TO_SAMPLE_RATE_RATIO=n/m)
        set_vals = compute_accum_set_values(config)

        # Normalize to [0, 1)
        phases = [v / config.ONE_FIXED for v in set_vals]

        print(f"\nNormalized phases:")
        for i, phase in enumerate(phases):
            ns_group = i // config.NS
            print(f"  Sample {i:2d} (group {ns_group}): {phase:.6f}")

        # Analyze clustering
        sorted_phases = sorted(phases)
        gaps = [sorted_phases[i+1] - sorted_phases[i] for i in range(len(sorted_phases)-1)]
        gaps.append(1.0 - sorted_phases[-1] + sorted_phases[0])  # Wrap-around gap

        print(f"\nPhase gap analysis:")
        print(f"  Min gap: {min(gaps):.6f}")
        print(f"  Max gap: {max(gaps):.6f}")
        print(f"  Ideal gap (uniform): {1.0/len(phases):.6f}")

        # Check for clustering (gaps < 1% of ideal)
        ideal_gap = 1.0 / len(phases)
        clustered = sum(1 for g in gaps if g < ideal_gap * 0.01)
        print(f"  Clustered pairs (gap < 1% of ideal): {clustered}")


if __name__ == "__main__":
    run_rtl_pattern_test()
    analyze_phase_distribution()

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("""
The RTL phase formula:
  accum_set_val[i] = ONE - RATIO + (ns_group * RATIO)

This formula has a known issue for ratios close to 1:
- For ratio=2/3: phases are well-distributed (0.333, 0.0, 0.667, ...)
- For ratio=0.995: phases cluster (0.005, 0.0, 0.995, 0.990, ...)

The simulation in tx_fsrc_sim_v2.py with --phase-mode rtl matches this
RTL behavior exactly. The HYBRID mode is an improvement that spreads
phases more evenly for high ratios while preserving good behavior for
normal ratios.

To match RTL exactly, use: --phase-mode rtl
""")
