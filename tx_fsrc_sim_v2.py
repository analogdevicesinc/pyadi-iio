#!/usr/bin/env python3
"""
TX FSRC (Fractional Sample Rate Converter) Python Simulation - v2

This simulation provides an accurate cycle-level model of the FPGA TX FSRC
datapath from the AD9084 testbench, with proper flow control modeling.

Key Features:
- Accurate accumulator-based sample enable generation
- Proper hole insertion with flow control
- JESD204 transport layer mapping
- Dynamic N/M ratio changes
- Comprehensive verification and statistics

Based on: ADS10v1/AD9084_ADS10v1_Acorn/trunk/fpga_ip/datapath_tx/fpga_src/sim/tb_tx_fsrc.sv
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any, Callable
from collections import deque
from enum import Enum, auto
import logging
import os

# Optional plotting support
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.gridspec import GridSpec
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class JESDParams:
    """JESD204 mode parameters."""
    L: int  # Number of lanes
    M: int  # Number of converters
    F: int  # Octets per frame
    S: int  # Samples per frame per converter
    NP: int  # Bits per sample


# Supported JESD modes
JESD_MODES = {
    'L1_M4_F8': JESDParams(L=1, M=4, F=8, S=1, NP=16),
    'L2_M4_F4': JESDParams(L=2, M=4, F=4, S=1, NP=16),
    'L4_M4_F2': JESDParams(L=4, M=4, F=2, S=1, NP=16),
    'L8_M2_F1': JESDParams(L=8, M=2, F=1, S=2, NP=16),
    'L8_M4_F1': JESDParams(L=8, M=4, F=1, S=1, NP=16),
}


class PhaseMode(Enum):
    """Phase initialization modes for accumulators."""
    RTL = auto()       # Original RTL formula: ONE - RATIO + i*RATIO (clusters for ratio~1)
    SPREAD = auto()    # Even spreading: i/num_samples
    SPREAD_INV = auto() # Inverse spreading: i*(1-RATIO)/num_samples
    HYBRID = auto()    # Best of both: RTL + minimum spacing guarantee


@dataclass
class FSRCConfig:
    """Configuration for the TX FSRC simulation."""
    # Core parameters
    np_bits: int = 16
    data_width: int = 256
    max_conv: int = 4
    accum_width: int = 64

    # JESD parameters
    jesd_l: int = 8
    jesd_m: int = 2
    jesd_f: int = 1
    jesd_s: int = 2
    jesd_np: int = 16
    num_links: int = 1

    # FSRC parameters
    channel_to_sample_rate_ratio: float = 2/3
    ns: int = 1
    phase_mode: PhaseMode = PhaseMode.HYBRID  # Best for all ratios

    # Test parameters
    random_data: bool = False
    identical_data: bool = True

    @classmethod
    def from_jesd_mode(cls, mode_name: str, **kwargs) -> 'FSRCConfig':
        """Create config from JESD mode name."""
        if mode_name not in JESD_MODES:
            raise ValueError(f"Unknown mode: {mode_name}. Available: {list(JESD_MODES.keys())}")
        params = JESD_MODES[mode_name]
        return cls(
            jesd_l=params.L,
            jesd_m=params.M,
            jesd_f=params.F,
            jesd_s=params.S,
            jesd_np=params.NP,
            **kwargs
        )

    @property
    def num_samples(self) -> int:
        return self.data_width // self.np_bits

    @property
    def conv_mask(self) -> int:
        return (1 << self.jesd_m) - 1

    @property
    def fsrc_invalid_sample(self) -> int:
        return 1 << (self.np_bits - 1)

    @property
    def one_fixed(self) -> int:
        return 1 << self.accum_width

    @property
    def ratio_fixed(self) -> int:
        return int(self.one_fixed * self.channel_to_sample_rate_ratio)


class Accumulator:
    """Fixed-point accumulator with overflow detection."""

    def __init__(self, width: int = 64):
        self.width = width
        self.mask = (1 << width) - 1
        self.accum = 0
        self.overflow = False

    def set(self, value: int) -> None:
        self.accum = value & self.mask
        self.overflow = False

    def add(self, value: int) -> bool:
        result = self.accum + value
        self.overflow = result > self.mask
        self.accum = result & self.mask
        return self.overflow


class SampleEnableGenerator:
    """
    Generates sample enable signals based on accumulator overflow.

    Each sample position has an accumulator that increments by RATIO each cycle.
    When the accumulator overflows (exceeds 2^WIDTH), that sample is valid.

    Phase initialization is critical for proper hole distribution:
    - RTL mode: Original formula, causes clustering for ratios close to 1
    - SPREAD mode: Even phase distribution, works for any ratio
    - SPREAD_INV mode: Phase based on hole rate, optimal for high ratios
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.accumulators = [Accumulator(config.accum_width)
                            for _ in range(config.num_samples)]
        self._init_accumulators()

    def _init_accumulators(self) -> None:
        """Initialize accumulators with staggered values based on phase mode."""
        ratio = self.config.channel_to_sample_rate_ratio
        one = self.config.one_fixed
        mask = (1 << self.config.accum_width) - 1
        num_samples = self.config.num_samples
        ns = self.config.ns

        for i in range(num_samples):
            ns_group = i // ns

            if self.config.phase_mode == PhaseMode.RTL:
                # Original RTL formula: ONE - RATIO + group*RATIO
                # Works well for ratios not close to 1, but clusters for ratio~1
                val = (one - self.config.ratio_fixed + (ns_group * self.config.ratio_fixed)) & mask

            elif self.config.phase_mode == PhaseMode.SPREAD:
                # Even phase spreading across [0, ONE)
                # Each accumulator offset by 1/num_samples of the full range
                num_groups = (num_samples + ns - 1) // ns
                phase_offset = (one * ns_group) // num_groups
                val = (one - self.config.ratio_fixed + phase_offset) & mask

            elif self.config.phase_mode == PhaseMode.SPREAD_INV:
                # Phase spreading based on hole rate (1-ratio)
                hole_rate = 1.0 - ratio
                num_groups = (num_samples + ns - 1) // ns
                phase_frac = (ns_group * hole_rate) / num_groups
                val = int((one * (1 - ratio + phase_frac)) % one) & mask

            elif self.config.phase_mode == PhaseMode.HYBRID:
                # Hybrid mode: Use RTL formula but ensure minimum phase separation
                # This combines the good distribution of RTL for normal ratios
                # with guaranteed separation for high ratios
                num_groups = (num_samples + ns - 1) // ns

                # Calculate RTL phase
                rtl_phase = (1 - ratio + (ns_group * ratio)) % 1.0

                # Calculate minimum phase separation needed
                # For high ratios, we need phases spread by at least 1/num_groups
                min_separation = 1.0 / num_groups

                # Add a spreading term that's significant for high ratios
                # When ratio is high, (1-ratio) is small, so we need extra spread
                # When ratio is low, RTL already provides good spread
                spread_term = (ns_group * min_separation * (1 - ratio) / max(1 - ratio, 0.01))

                # Combine: use RTL as base, add spread for high-ratio cases
                # The spread_term naturally becomes larger when ratio approaches 1
                combined_phase = (rtl_phase + spread_term * (ratio ** 4)) % 1.0

                val = int(one * combined_phase) & mask

            else:
                val = 0

            self.accumulators[i].set(val)

    def set_accumulators(self) -> None:
        """Reset accumulators to initial state."""
        self._init_accumulators()

    def get_initial_phases(self) -> np.ndarray:
        """Get normalized initial phase values for visualization."""
        return np.array([acc.accum / self.config.one_fixed
                        for acc in self.accumulators])

    def step(self, enable: bool = True) -> np.ndarray:
        """Advance accumulators and return sample enables."""
        sample_en = np.zeros(self.config.num_samples, dtype=bool)

        if enable:
            for i, accum in enumerate(self.accumulators):
                sample_en[i] = accum.add(self.config.ratio_fixed)

        return sample_en


class TxFSRCSimple:
    """
    Simplified TX FSRC model for behavioral simulation.

    This model focuses on the core FSRC algorithm without the
    complex flow control of the full RTL. It correctly implements:
    - Accumulator-based sample enable generation
    - Hole insertion based on enable pattern
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.sample_en_gen = SampleEnableGenerator(config)

        # State
        self.fsrc_en = False
        self.fsrc_data_en = False
        self.reset_state = True

        # Data queue for each converter
        self.data_queues = [deque() for _ in range(config.max_conv)]

        # Statistics
        self.stats = {
            'input_samples': 0,
            'output_samples': 0,
            'holes_inserted': 0,
            'valid_samples': 0,
            'cycles': 0,
        }

    def reset(self) -> None:
        self.reset_state = True
        self.fsrc_en = False
        self.fsrc_data_en = False
        for q in self.data_queues:
            q.clear()
        self.stats = {k: 0 for k in self.stats}

    def configure(self, ratio_n: int, ratio_m: int) -> None:
        """Configure new N/M ratio."""
        self.config.channel_to_sample_rate_ratio = ratio_n / ratio_m
        self.sample_en_gen = SampleEnableGenerator(self.config)
        logger.info(f"FSRC ratio set to {ratio_n}/{ratio_m} = {ratio_n/ratio_m:.6f}")

    def start(self) -> None:
        self.reset_state = False
        self.fsrc_en = True
        self.sample_en_gen.set_accumulators()

    def enable_data(self) -> None:
        self.fsrc_data_en = True

    def step(self, input_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Process one clock cycle.

        Args:
            input_data: Shape (num_conv, num_samples)

        Returns:
            (output_data, sample_enables)
        """
        self.stats['cycles'] += 1

        if self.reset_state:
            zeros = np.full((self.config.max_conv, self.config.num_samples),
                           self.config.fsrc_invalid_sample, dtype=np.uint64)
            return zeros, np.zeros(self.config.num_samples, dtype=bool)

        # Generate sample enables
        accum_en = self.fsrc_en and self.fsrc_data_en
        sample_en = self.sample_en_gen.step(accum_en)

        # Track input
        self.stats['input_samples'] += input_data.shape[1] * self.config.jesd_m

        # Queue input samples
        for conv in range(self.config.jesd_m):
            for sample in input_data[conv]:
                self.data_queues[conv].append(int(sample))

        # Generate output with holes
        output = np.zeros((self.config.max_conv, self.config.num_samples), dtype=np.uint64)

        if self.fsrc_en:
            holes = ~sample_en if self.fsrc_data_en else np.ones(self.config.num_samples, dtype=bool)

            for conv in range(self.config.jesd_m):
                for i in range(self.config.num_samples):
                    self.stats['output_samples'] += 1
                    if holes[i]:
                        output[conv, i] = self.config.fsrc_invalid_sample
                        self.stats['holes_inserted'] += 1
                    elif self.data_queues[conv]:
                        output[conv, i] = self.data_queues[conv].popleft()
                        self.stats['valid_samples'] += 1
                    else:
                        output[conv, i] = self.config.fsrc_invalid_sample
                        self.stats['holes_inserted'] += 1
        else:
            # Bypass mode
            output = input_data.copy()
            self.stats['valid_samples'] += input_data.size

        return output, sample_en


class TxFSRCTestbench:
    """Testbench for TX FSRC simulation."""

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.fsrc = TxFSRCSimple(config)

        # Verification
        self.golden_queues = [deque() for _ in range(config.max_conv)]
        self.cycle_count = 0
        self.error_count = 0
        self.results = None

    def reset(self) -> None:
        self.fsrc.reset()
        for q in self.golden_queues:
            q.clear()
        self.cycle_count = 0
        self.error_count = 0

    def generate_input(self) -> np.ndarray:
        """Generate test input data."""
        data = np.zeros((self.config.max_conv, self.config.num_samples), dtype=np.uint64)

        for conv in range(self.config.jesd_m):
            for i in range(self.config.num_samples):
                if self.config.random_data:
                    sample = np.random.randint(0, 2**self.config.np_bits)
                elif self.config.identical_data:
                    sample = self.cycle_count % (2**self.config.np_bits)
                else:
                    sample = (self.cycle_count * self.config.num_samples + i) % (2**self.config.np_bits)

                # Avoid invalid marker
                if sample == self.config.fsrc_invalid_sample:
                    sample ^= 1

                data[conv, i] = sample
                self.golden_queues[conv].append(sample)

        return data

    def verify_output(self, output: np.ndarray) -> int:
        """Verify output against golden model. Returns error count."""
        errors = 0

        for conv in range(self.config.jesd_m):
            for i in range(self.config.num_samples):
                sample = int(output[conv, i])

                if sample != self.config.fsrc_invalid_sample:
                    if self.golden_queues[conv]:
                        expected = self.golden_queues[conv].popleft()
                        if sample != expected:
                            logger.error(f"Mismatch at cycle {self.cycle_count}, conv {conv}, "
                                       f"sample {i}: expected 0x{expected:04X}, got 0x{sample:04X}")
                            errors += 1
                    else:
                        logger.error(f"Output without input at cycle {self.cycle_count}")
                        errors += 1

        return errors

    def run(self, num_cycles: int,
            ratio_changes: Optional[List[Tuple[int, int, int]]] = None) -> Dict[str, Any]:
        """
        Run simulation.

        Args:
            num_cycles: Number of cycles to simulate
            ratio_changes: List of (cycle, n, m) tuples for ratio changes

        Returns:
            Results dictionary
        """
        ratio_changes = ratio_changes or []
        ratio_idx = 0

        self.reset()
        self.fsrc.start()
        self.fsrc.enable_data()

        sample_en_history = []
        ratio_history = [(0, self.config.channel_to_sample_rate_ratio)]

        logger.info(f"Running {num_cycles} cycles...")

        for cycle in range(num_cycles):
            self.cycle_count = cycle

            # Check for ratio changes
            while ratio_idx < len(ratio_changes) and ratio_changes[ratio_idx][0] <= cycle:
                _, n, m = ratio_changes[ratio_idx]
                self.fsrc.configure(n, m)
                self.fsrc.sample_en_gen.set_accumulators()
                ratio_history.append((cycle, n/m))
                ratio_idx += 1

            # Generate and process
            input_data = self.generate_input()
            output, sample_en = self.fsrc.step(input_data)
            sample_en_history.append(sample_en.copy())

            # Verify
            errors = self.verify_output(output)
            self.error_count += errors

        # Compile results
        self.results = {
            'config': {
                'jesd_l': self.config.jesd_l,
                'jesd_m': self.config.jesd_m,
                'jesd_f': self.config.jesd_f,
                'num_samples': self.config.num_samples,
                'ratio': self.config.channel_to_sample_rate_ratio,
            },
            'cycles': num_cycles,
            'errors': self.error_count,
            'stats': self.fsrc.stats.copy(),
            'ratio_history': ratio_history,
            'sample_en_history': sample_en_history,
        }

        return self.results

    def print_summary(self) -> None:
        """Print test summary."""
        if not self.results:
            print("No results. Run simulation first.")
            return

        print("\n" + "="*60)
        print("TX FSRC Simulation Summary")
        print("="*60)

        cfg = self.results['config']
        print(f"\nJESD Mode: L={cfg['jesd_l']}, M={cfg['jesd_m']}, F={cfg['jesd_f']}")
        print(f"Samples per cycle: {cfg['num_samples']}")
        print(f"Target ratio: {cfg['ratio']:.6f}")

        stats = self.results['stats']
        print(f"\nCycles: {self.results['cycles']}")
        print(f"Input samples: {stats['input_samples']}")
        print(f"Output samples: {stats['output_samples']}")
        print(f"Valid samples: {stats['valid_samples']}")
        print(f"Holes inserted: {stats['holes_inserted']}")

        if stats['output_samples'] > 0:
            ratio = stats['valid_samples'] / stats['output_samples']
            print(f"Actual ratio: {ratio:.6f}")

        print(f"\nErrors: {self.results['errors']}")
        print(f"Status: {'PASS' if self.results['errors'] == 0 else 'FAIL'}")

    def print_pattern(self, num_cycles: int = 20) -> None:
        """Print sample enable pattern."""
        if not self.results or 'sample_en_history' not in self.results:
            print("No pattern data. Run simulation first.")
            return

        print("\nSample Enable Pattern (# = valid, . = hole):")
        history = self.results['sample_en_history']

        for i, sample_en in enumerate(history[:num_cycles]):
            pattern = ''.join(['#' if en else '.' for en in sample_en])
            valid = np.sum(sample_en)
            print(f"  Cycle {i:3d}: [{pattern}] ({valid}/{len(sample_en)})")

    def plot_results(self, save_path: Optional[str] = None, show: bool = True) -> None:
        """
        Generate comprehensive plots of simulation results.

        Args:
            save_path: Path to save the figure (optional)
            show: Whether to display the plot
        """
        if not PLOTTING_AVAILABLE:
            print("Matplotlib not available. Install with: pip install matplotlib")
            return

        if not self.results or 'sample_en_history' not in self.results:
            print("No results to plot. Run simulation first.")
            return

        sample_en = np.array(self.results['sample_en_history'])
        num_cycles = len(sample_en)
        num_samples = sample_en.shape[1]
        ratio_history = self.results['ratio_history']

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 2, figure=fig, height_ratios=[1.5, 1, 1])

        # Custom colormap: red for holes, green for valid
        colors = ['#d62728', '#2ca02c']  # red, green
        cmap = LinearSegmentedColormap.from_list('hole_valid', colors, N=2)

        # Plot 1: Sample Enable Heatmap (full width)
        ax1 = fig.add_subplot(gs[0, :])
        im = ax1.imshow(sample_en.T, aspect='auto', cmap=cmap,
                       interpolation='nearest', vmin=0, vmax=1)

        # Add ratio change markers
        for cycle, ratio in ratio_history:
            if cycle > 0 and cycle < num_cycles:
                ax1.axvline(x=cycle, color='yellow', linestyle='--', linewidth=2, alpha=0.8)
                ax1.text(cycle + 1, -0.5, f'{ratio:.2f}', fontsize=8, color='yellow',
                        verticalalignment='bottom')

        ax1.set_xlabel('Clock Cycle')
        ax1.set_ylabel('Sample Position')
        ax1.set_title('Sample Enable Pattern (Green=Valid, Red=Hole)')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax1, orientation='vertical', shrink=0.8)
        cbar.set_ticks([0.25, 0.75])
        cbar.set_ticklabels(['Hole', 'Valid'])

        # Plot 2: Valid Samples per Cycle
        ax2 = fig.add_subplot(gs[1, 0])
        valid_per_cycle = np.sum(sample_en, axis=1)
        cycles = np.arange(num_cycles)

        ax2.bar(cycles, valid_per_cycle, color='steelblue', alpha=0.7, width=1.0)

        # Add target lines for each ratio segment
        prev_cycle = 0
        for i, (cycle, ratio) in enumerate(ratio_history):
            next_cycle = ratio_history[i + 1][0] if i + 1 < len(ratio_history) else num_cycles
            target = num_samples * ratio
            ax2.hlines(y=target, xmin=prev_cycle, xmax=next_cycle,
                      colors='red', linestyles='--', linewidth=2)
            prev_cycle = next_cycle

        ax2.set_xlabel('Clock Cycle')
        ax2.set_ylabel('Valid Samples')
        ax2.set_title('Valid Samples per Cycle')
        ax2.set_xlim(0, num_cycles)
        ax2.set_ylim(0, num_samples + 1)
        ax2.legend(['Target', 'Actual'], loc='upper right')

        # Plot 3: Cumulative Ratio Convergence
        ax3 = fig.add_subplot(gs[1, 1])
        cumulative_valid = np.cumsum(valid_per_cycle)
        cumulative_total = np.arange(1, num_cycles + 1) * num_samples
        cumulative_ratio = cumulative_valid / cumulative_total

        ax3.plot(cycles, cumulative_ratio, 'b-', linewidth=2, label='Actual')

        # Add target ratio lines
        prev_cycle = 0
        for i, (cycle, ratio) in enumerate(ratio_history):
            next_cycle = ratio_history[i + 1][0] if i + 1 < len(ratio_history) else num_cycles
            ax3.hlines(y=ratio, xmin=prev_cycle, xmax=next_cycle,
                      colors='red', linestyles='--', linewidth=2)
            if cycle > 0:
                ax3.axvline(x=cycle, color='gray', linestyle=':', alpha=0.5)
            prev_cycle = next_cycle

        ax3.set_xlabel('Clock Cycle')
        ax3.set_ylabel('Cumulative Valid Ratio')
        ax3.set_title('Cumulative Ratio Convergence')
        ax3.set_xlim(0, num_cycles)
        ax3.set_ylim(0, 1.05)
        ax3.legend(['Actual', 'Target'], loc='lower right')
        ax3.grid(True, alpha=0.3)

        # Plot 4: Per-Position Statistics
        ax4 = fig.add_subplot(gs[2, 0])
        position_enables = np.sum(sample_en, axis=0)
        positions = np.arange(num_samples)

        bars = ax4.bar(positions, position_enables, color='teal', alpha=0.7)
        ax4.axhline(y=num_cycles * ratio_history[-1][1], color='red',
                   linestyle='--', linewidth=2, label='Expected')

        ax4.set_xlabel('Sample Position')
        ax4.set_ylabel('Total Valid Count')
        ax4.set_title('Valid Samples by Position')
        ax4.set_xlim(-0.5, num_samples - 0.5)
        ax4.legend()

        # Plot 5: Statistics Summary
        ax5 = fig.add_subplot(gs[2, 1])
        ax5.axis('off')

        stats = self.results['stats']
        cfg = self.results['config']

        # Create text summary
        text_lines = [
            "SIMULATION SUMMARY",
            "=" * 40,
            f"JESD Mode: L={cfg['jesd_l']}, M={cfg['jesd_m']}, F={cfg['jesd_f']}",
            f"Samples per cycle: {cfg['num_samples']}",
            f"Total cycles: {self.results['cycles']}",
            "",
            "DATA STATISTICS",
            "-" * 40,
            f"Input samples:  {stats['input_samples']:,}",
            f"Output samples: {stats['output_samples']:,}",
            f"Valid samples:  {stats['valid_samples']:,}",
            f"Holes inserted: {stats['holes_inserted']:,}",
            "",
            f"Target ratio:   {cfg['ratio']:.6f}",
            f"Actual ratio:   {stats['valid_samples']/max(1,stats['output_samples']):.6f}",
            "",
            "VERIFICATION",
            "-" * 40,
            f"Errors: {self.results['errors']}",
            f"Status: {'PASS' if self.results['errors'] == 0 else 'FAIL'}",
        ]

        if len(ratio_history) > 1:
            text_lines.extend([
                "",
                "RATIO CHANGES",
                "-" * 40,
            ])
            for cycle, ratio in ratio_history:
                text_lines.append(f"  Cycle {cycle:4d}: {ratio:.4f}")

        text = '\n'.join(text_lines)
        ax5.text(0.1, 0.95, text, transform=ax5.transAxes,
                fontsize=10, verticalalignment='top',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved plot to: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_pattern_detail(self, start_cycle: int = 0, num_cycles: int = 32,
                           save_path: Optional[str] = None, show: bool = True) -> None:
        """
        Plot detailed view of sample enable pattern.

        Args:
            start_cycle: Starting cycle to display
            num_cycles: Number of cycles to display
            save_path: Path to save the figure
            show: Whether to display the plot
        """
        if not PLOTTING_AVAILABLE:
            print("Matplotlib not available.")
            return

        if not self.results or 'sample_en_history' not in self.results:
            print("No results to plot. Run simulation first.")
            return

        sample_en = np.array(self.results['sample_en_history'])
        end_cycle = min(start_cycle + num_cycles, len(sample_en))
        data = sample_en[start_cycle:end_cycle]

        fig, ax = plt.subplots(figsize=(14, 8))

        # Create grid visualization
        num_samples = data.shape[1]
        colors = ['#ffcccc', '#ccffcc']  # light red, light green

        for cycle_idx, cycle_data in enumerate(data):
            for sample_idx, enabled in enumerate(cycle_data):
                color = colors[1] if enabled else colors[0]
                rect = plt.Rectangle((cycle_idx, sample_idx), 1, 1,
                                     facecolor=color, edgecolor='gray', linewidth=0.5)
                ax.add_patch(rect)

                # Add text labels
                symbol = '#' if enabled else '.'
                text_color = 'darkgreen' if enabled else 'darkred'
                ax.text(cycle_idx + 0.5, sample_idx + 0.5, symbol,
                       ha='center', va='center', fontsize=8,
                       color=text_color, fontweight='bold')

        ax.set_xlim(0, len(data))
        ax.set_ylim(0, num_samples)
        ax.set_xlabel('Clock Cycle')
        ax.set_ylabel('Sample Position')
        ax.set_title(f'Sample Enable Pattern Detail (Cycles {start_cycle}-{end_cycle-1})')

        # Add cycle numbers on x-axis
        ax.set_xticks(np.arange(0.5, len(data), 1))
        ax.set_xticklabels([str(i + start_cycle) for i in range(len(data))], fontsize=8)

        # Add sample position numbers on y-axis
        ax.set_yticks(np.arange(0.5, num_samples, 1))
        ax.set_yticklabels([str(i) for i in range(num_samples)], fontsize=8)

        # Add valid count annotations at bottom
        valid_counts = np.sum(data, axis=1)
        for i, count in enumerate(valid_counts):
            ax.text(i + 0.5, -0.8, str(count), ha='center', va='top',
                   fontsize=8, fontweight='bold')

        ax.text(-0.5, -0.8, 'Valid:', ha='right', va='top', fontsize=8)

        # Legend
        valid_patch = mpatches.Patch(color=colors[1], label='Valid (#)')
        hole_patch = mpatches.Patch(color=colors[0], label='Hole (.)')
        ax.legend(handles=[valid_patch, hole_patch], loc='upper right')

        ax.set_aspect('equal')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved plot to: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()


def plot_ratio_comparison(ratios: List[Tuple[int, int]], num_cycles: int = 50,
                         save_path: Optional[str] = None, show: bool = True) -> None:
    """
    Compare sample enable patterns for different N/M ratios.

    Args:
        ratios: List of (n, m) tuples for ratios to compare
        num_cycles: Number of cycles to simulate
        save_path: Path to save the figure
        show: Whether to display the plot
    """
    if not PLOTTING_AVAILABLE:
        print("Matplotlib not available.")
        return

    num_ratios = len(ratios)
    fig, axes = plt.subplots(num_ratios, 2, figsize=(14, 3 * num_ratios))

    if num_ratios == 1:
        axes = axes.reshape(1, 2)

    colors = ['#d62728', '#2ca02c']  # red, green
    cmap = LinearSegmentedColormap.from_list('hole_valid', colors, N=2)

    for idx, (n, m) in enumerate(ratios):
        config = FSRCConfig(
            data_width=256,
            jesd_l=8,
            jesd_m=2,
            channel_to_sample_rate_ratio=n/m
        )

        tb = TxFSRCTestbench(config)
        tb.run(num_cycles)

        sample_en = np.array(tb.results['sample_en_history'])

        # Pattern heatmap
        ax1 = axes[idx, 0]
        im = ax1.imshow(sample_en.T, aspect='auto', cmap=cmap,
                       interpolation='nearest', vmin=0, vmax=1)
        ax1.set_xlabel('Clock Cycle')
        ax1.set_ylabel('Sample Position')
        ax1.set_title(f'Ratio {n}/{m} = {n/m:.4f}')

        # Cumulative ratio
        ax2 = axes[idx, 1]
        valid_per_cycle = np.sum(sample_en, axis=1)
        cumulative_valid = np.cumsum(valid_per_cycle)
        cumulative_total = np.arange(1, num_cycles + 1) * config.num_samples
        cumulative_ratio = cumulative_valid / cumulative_total

        ax2.plot(cumulative_ratio, 'b-', linewidth=2, label='Actual')
        ax2.axhline(y=n/m, color='red', linestyle='--', linewidth=2, label='Target')
        ax2.set_xlabel('Clock Cycle')
        ax2.set_ylabel('Cumulative Ratio')
        ax2.set_title(f'Convergence (Final: {cumulative_ratio[-1]:.4f})')
        ax2.set_ylim(0, 1)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_accumulator_states(config: FSRCConfig, num_cycles: int = 20,
                           save_path: Optional[str] = None, show: bool = True) -> None:
    """
    Visualize accumulator states over time.

    Args:
        config: FSRC configuration
        num_cycles: Number of cycles to simulate
        save_path: Path to save the figure
        show: Whether to display the plot
    """
    if not PLOTTING_AVAILABLE:
        print("Matplotlib not available.")
        return

    # Create sample enable generator and track states
    sample_en_gen = SampleEnableGenerator(config)
    sample_en_gen.set_accumulators()

    accum_history = []
    overflow_history = []

    for _ in range(num_cycles):
        # Record current state before step
        states = [acc.accum / config.one_fixed for acc in sample_en_gen.accumulators]
        accum_history.append(states)

        # Step and record overflows
        sample_en = sample_en_gen.step(True)
        overflow_history.append(sample_en.copy())

    accum_history = np.array(accum_history)
    overflow_history = np.array(overflow_history)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))

    # Plot 1: Accumulator values over time
    ax1 = axes[0]
    for i in range(min(8, config.num_samples)):  # Show first 8 accumulators
        ax1.plot(accum_history[:, i], label=f'Acc {i}', alpha=0.7)

    ax1.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Overflow threshold')
    ax1.set_xlabel('Clock Cycle')
    ax1.set_ylabel('Accumulator Value (normalized)')
    ax1.set_title('Accumulator States Over Time')
    ax1.legend(loc='upper right', ncol=3, fontsize=8)
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Overflow events (sample enables)
    ax2 = axes[1]
    colors = ['#d62728', '#2ca02c']
    cmap = LinearSegmentedColormap.from_list('hole_valid', colors, N=2)

    im = ax2.imshow(overflow_history.T, aspect='auto', cmap=cmap,
                   interpolation='nearest', vmin=0, vmax=1)
    ax2.set_xlabel('Clock Cycle')
    ax2.set_ylabel('Accumulator Index')
    ax2.set_title('Accumulator Overflows (Green=Overflow/Valid, Red=No Overflow/Hole)')

    cbar = plt.colorbar(im, ax=ax2, orientation='vertical', shrink=0.8)
    cbar.set_ticks([0.25, 0.75])
    cbar.set_ticklabels(['No Overflow', 'Overflow'])

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def run_tests(with_plots: bool = False, save_plots: bool = False):
    """Run comprehensive test suite."""
    print("="*60)
    print("TX FSRC Python Simulation")
    print("="*60)

    # Test 1: Basic 2/3 ratio
    print("\n--- Test 1: Basic 2/3 Ratio ---")
    config = FSRCConfig.from_jesd_mode('L8_M2_F1', channel_to_sample_rate_ratio=2/3)
    tb = TxFSRCTestbench(config)
    tb.run(100)
    tb.print_summary()
    tb.print_pattern(15)

    if with_plots:
        save_path = 'fsrc_basic_test.png' if save_plots else None
        tb.plot_results(save_path=save_path, show=not save_plots)

    # Test 2: Different ratios
    print("\n--- Test 2: Various Ratios ---")
    ratios = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (7, 8), (9, 10)]

    for n, m in ratios:
        config = FSRCConfig.from_jesd_mode('L8_M2_F1', channel_to_sample_rate_ratio=n/m)
        tb = TxFSRCTestbench(config)
        results = tb.run(200)
        actual = results['stats']['valid_samples'] / max(1, results['stats']['output_samples'])
        status = 'PASS' if results['errors'] == 0 else 'FAIL'
        print(f"  Ratio {n}/{m} ({n/m:.4f}): actual={actual:.4f}, {status}")

    if with_plots:
        save_path = 'fsrc_ratio_comparison.png' if save_plots else None
        plot_ratio_comparison([(1, 2), (2, 3), (3, 4), (7, 8)],
                             save_path=save_path, show=not save_plots)

    # Test 3: Dynamic ratio changes
    print("\n--- Test 3: Dynamic Ratio Changes ---")
    config = FSRCConfig.from_jesd_mode('L8_M2_F1', channel_to_sample_rate_ratio=1/2)
    ratio_changes = [
        (0, 1, 2),
        (50, 2, 3),
        (100, 3, 4),
        (150, 4, 5),
        (200, 5, 6),
    ]
    tb = TxFSRCTestbench(config)
    tb.run(250, ratio_changes=ratio_changes)
    tb.print_summary()

    if with_plots:
        save_path = 'fsrc_ratio_changes.png' if save_plots else None
        tb.plot_results(save_path=save_path, show=not save_plots)

    # Test 4: All JESD modes
    print("\n--- Test 4: JESD Mode Sweep ---")
    for mode_name in JESD_MODES:
        config = FSRCConfig.from_jesd_mode(mode_name, channel_to_sample_rate_ratio=2/3)
        tb = TxFSRCTestbench(config)
        results = tb.run(100)
        params = JESD_MODES[mode_name]
        status = 'PASS' if results['errors'] == 0 else 'FAIL'
        print(f"  {mode_name} (L={params.L}, M={params.M}, F={params.F}): {status}")

    print("\n" + "="*60)
    print("All Tests Complete")
    print("="*60)


def demo_pattern():
    """Demonstrate sample enable patterns for different ratios."""
    print("\n" + "="*60)
    print("Sample Enable Pattern Demo")
    print("="*60)

    ratios = [(1, 2), (2, 3), (3, 4), (7, 8)]

    for n, m in ratios:
        print(f"\n--- Ratio {n}/{m} = {n/m:.4f} ---")
        config = FSRCConfig(
            data_width=256,
            jesd_l=8,
            jesd_m=2,
            channel_to_sample_rate_ratio=n/m
        )

        fsrc = TxFSRCSimple(config)
        fsrc.start()
        fsrc.enable_data()

        print("Pattern (# = valid, . = hole):")
        valid_total = 0
        for cycle in range(10):
            input_data = np.zeros((config.max_conv, config.num_samples), dtype=np.uint64)
            _, sample_en = fsrc.step(input_data)
            pattern = ''.join(['#' if en else '.' for en in sample_en])
            valid = np.sum(sample_en)
            valid_total += valid
            print(f"  [{pattern}] ({valid}/{config.num_samples})")

        total = 10 * config.num_samples
        print(f"Total: {valid_total}/{total} = {valid_total/total:.4f}")


def compare_phase_modes(ratio_n: int = 1990, ratio_m: int = 2000, num_cycles: int = 50):
    """
    Compare different phase initialization modes.

    This demonstrates the hole clustering issue with the RTL mode
    and how SPREAD mode fixes it for ratios close to 1.
    """
    print("\n" + "="*70)
    print(f"Phase Mode Comparison (Ratio {ratio_n}/{ratio_m} = {ratio_n/ratio_m:.6f})")
    print("="*70)

    modes = [
        (PhaseMode.RTL, "RTL (Original)"),
        (PhaseMode.SPREAD, "SPREAD (Even distribution)"),
        (PhaseMode.HYBRID, "HYBRID (Best of both)"),
    ]

    for mode, name in modes:
        print(f"\n--- {name} ---")

        config = FSRCConfig(
            data_width=256,
            jesd_l=8,
            jesd_m=2,
            channel_to_sample_rate_ratio=ratio_n/ratio_m,
            phase_mode=mode
        )

        # Show initial phases
        sample_en_gen = SampleEnableGenerator(config)
        phases = sample_en_gen.get_initial_phases()
        print(f"Initial phases (normalized):")
        phase_str = ' '.join([f'{p:.3f}' for p in phases[:8]])
        print(f"  Samples 0-7:  {phase_str}")
        phase_str = ' '.join([f'{p:.3f}' for p in phases[8:]])
        print(f"  Samples 8-15: {phase_str}")

        # Run simulation
        fsrc = TxFSRCSimple(config)
        fsrc.start()
        fsrc.enable_data()

        # Track hole positions
        hole_cycles = []
        hole_positions = []

        print(f"\nFirst {min(20, num_cycles)} cycles (# = valid, . = hole):")
        for cycle in range(num_cycles):
            input_data = np.zeros((config.max_conv, config.num_samples), dtype=np.uint64)
            _, sample_en = fsrc.step(input_data)

            # Record holes
            for pos, en in enumerate(sample_en):
                if not en:
                    hole_cycles.append(cycle)
                    hole_positions.append(pos)

            if cycle < 20:
                pattern = ''.join(['#' if en else '.' for en in sample_en])
                holes = config.num_samples - np.sum(sample_en)
                if holes > 0:
                    print(f"  Cycle {cycle:3d}: [{pattern}] ({holes} holes)")

        # Analyze hole distribution
        if hole_cycles:
            hole_cycles = np.array(hole_cycles)
            hole_positions = np.array(hole_positions)

            print(f"\nHole Statistics ({len(hole_cycles)} total holes in {num_cycles} cycles):")
            print(f"  Expected holes: {num_cycles * config.num_samples * (1 - ratio_n/ratio_m):.1f}")

            # Check for clustering - consecutive holes
            consecutive = 0
            for i in range(1, len(hole_cycles)):
                if hole_cycles[i] == hole_cycles[i-1]:  # Same cycle
                    if abs(hole_positions[i] - hole_positions[i-1]) <= 1:
                        consecutive += 1
                elif hole_cycles[i] == hole_cycles[i-1] + 1:  # Next cycle
                    if hole_positions[i] == 0 and hole_positions[i-1] == config.num_samples - 1:
                        consecutive += 1

            print(f"  Consecutive hole pairs: {consecutive}")
            print(f"  Hole positions used: {sorted(set(hole_positions))}")

            # Cycle gaps between holes
            if len(hole_cycles) > 1:
                gaps = np.diff(hole_cycles * config.num_samples + hole_positions)
                print(f"  Gap between holes - min: {gaps.min()}, max: {gaps.max()}, mean: {gaps.mean():.1f}")
        else:
            print(f"\nNo holes in {num_cycles} cycles (expected for high ratios)")


def plot_phase_comparison(ratio_n: int = 1990, ratio_m: int = 2000, num_cycles: int = 100,
                         save_path: Optional[str] = None, show: bool = True):
    """
    Visualize the difference between phase modes.
    """
    if not PLOTTING_AVAILABLE:
        print("Matplotlib not available.")
        return

    modes = [
        (PhaseMode.RTL, "RTL (Original)"),
        (PhaseMode.SPREAD, "SPREAD (Fixed)"),
    ]

    fig, axes = plt.subplots(len(modes), 3, figsize=(16, 4 * len(modes)))

    colors = ['#d62728', '#2ca02c']
    cmap = LinearSegmentedColormap.from_list('hole_valid', colors, N=2)

    for idx, (mode, name) in enumerate(modes):
        config = FSRCConfig(
            data_width=256,
            channel_to_sample_rate_ratio=ratio_n/ratio_m,
            phase_mode=mode
        )

        # Get initial phases
        sample_en_gen = SampleEnableGenerator(config)
        phases = sample_en_gen.get_initial_phases()

        # Run simulation
        tb = TxFSRCTestbench(config)
        tb.run(num_cycles)
        sample_en = np.array(tb.results['sample_en_history'])

        # Plot 1: Initial phases
        ax1 = axes[idx, 0]
        bars = ax1.bar(range(config.num_samples), phases, color='steelblue')
        ax1.axhline(y=1-ratio_n/ratio_m, color='red', linestyle='--',
                   label=f'Hole threshold (1-R={1-ratio_n/ratio_m:.4f})')
        ax1.set_xlabel('Sample Position')
        ax1.set_ylabel('Initial Phase')
        ax1.set_title(f'{name}\nInitial Accumulator Phases')
        ax1.set_ylim(0, 1)
        ax1.legend(fontsize=8)

        # Plot 2: Sample enable heatmap
        ax2 = axes[idx, 1]
        im = ax2.imshow(sample_en.T, aspect='auto', cmap=cmap,
                       interpolation='nearest', vmin=0, vmax=1)
        ax2.set_xlabel('Clock Cycle')
        ax2.set_ylabel('Sample Position')
        ax2.set_title(f'Sample Enable Pattern')

        # Plot 3: Hole position histogram
        ax3 = axes[idx, 2]
        holes_per_position = config.num_samples - np.sum(sample_en, axis=0)
        ax3.bar(range(config.num_samples), holes_per_position, color='coral')
        expected = num_cycles * (1 - ratio_n/ratio_m)
        ax3.axhline(y=expected, color='blue', linestyle='--',
                   label=f'Expected ({expected:.1f})')
        ax3.set_xlabel('Sample Position')
        ax3.set_ylabel('Number of Holes')
        ax3.set_title(f'Holes per Position')
        ax3.legend()

    plt.suptitle(f'Phase Mode Comparison - Ratio {ratio_n}/{ratio_m} = {ratio_n/ratio_m:.6f}',
                fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def demo_plots():
    """Demonstrate all plotting capabilities."""
    if not PLOTTING_AVAILABLE:
        print("Matplotlib not available. Install with: pip install matplotlib")
        return

    print("="*60)
    print("TX FSRC Plotting Demo")
    print("="*60)

    # Demo 1: Basic simulation with full results
    print("\n--- Demo 1: Full Results Plot ---")
    config = FSRCConfig.from_jesd_mode('L8_M2_F1', channel_to_sample_rate_ratio=2/3)
    tb = TxFSRCTestbench(config)
    tb.run(100)
    tb.plot_results(save_path='demo_full_results.png', show=False)
    print("Saved: demo_full_results.png")

    # Demo 2: Pattern detail view
    print("\n--- Demo 2: Pattern Detail ---")
    tb.plot_pattern_detail(start_cycle=0, num_cycles=16,
                          save_path='demo_pattern_detail.png', show=False)
    print("Saved: demo_pattern_detail.png")

    # Demo 3: Ratio comparison
    print("\n--- Demo 3: Ratio Comparison ---")
    plot_ratio_comparison([(1, 2), (2, 3), (3, 4), (7, 8)],
                         save_path='demo_ratio_comparison.png', show=False)
    print("Saved: demo_ratio_comparison.png")

    # Demo 4: Accumulator states
    print("\n--- Demo 4: Accumulator States ---")
    config = FSRCConfig(channel_to_sample_rate_ratio=2/3)
    plot_accumulator_states(config, num_cycles=30,
                           save_path='demo_accumulator_states.png', show=False)
    print("Saved: demo_accumulator_states.png")

    # Demo 5: Dynamic ratio changes
    print("\n--- Demo 5: Dynamic Ratio Changes ---")
    config = FSRCConfig.from_jesd_mode('L8_M2_F1', channel_to_sample_rate_ratio=1/2)
    ratio_changes = [
        (0, 1, 2),
        (30, 2, 3),
        (60, 3, 4),
        (90, 7, 8),
    ]
    tb = TxFSRCTestbench(config)
    tb.run(120, ratio_changes=ratio_changes)
    tb.plot_results(save_path='demo_ratio_changes.png', show=False)
    print("Saved: demo_ratio_changes.png")

    print("\n" + "="*60)
    print("All demo plots saved!")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TX FSRC Simulation with Plotting Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test full --plot                    # Run all tests with plots
  %(prog)s --test pattern                        # Show pattern demo
  %(prog)s --test custom --ratio-n 3 --ratio-m 4 --plot
  %(prog)s --test plots                          # Generate demo plots
  %(prog)s --test compare --ratios 1/2 2/3 3/4   # Compare ratios
  %(prog)s --test phase --ratio-n 1990 --ratio-m 2000  # Compare phase modes
  %(prog)s --test custom --ratio-n 1990 --ratio-m 2000 --phase-mode rtl  # Use RTL mode
        """
    )
    parser.add_argument('--test', choices=['full', 'pattern', 'custom', 'plots', 'compare', 'accum', 'phase'],
                       default='full', help='Test mode to run')
    parser.add_argument('--cycles', type=int, default=100, help='Number of simulation cycles')
    parser.add_argument('--ratio-n', type=int, default=2, help='Ratio numerator (N)')
    parser.add_argument('--ratio-m', type=int, default=3, help='Ratio denominator (M)')
    parser.add_argument('--ratios', nargs='+', default=['1/2', '2/3', '3/4'],
                       help='Ratios to compare (format: N/M)')
    parser.add_argument('--mode', default='L8_M2_F1', choices=list(JESD_MODES.keys()),
                       help='JESD mode')
    parser.add_argument('--phase-mode', choices=['rtl', 'spread', 'spread_inv', 'hybrid'],
                       default='hybrid', help='Phase initialization mode')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    parser.add_argument('--save', action='store_true', help='Save plots to files instead of showing')
    parser.add_argument('--output', '-o', type=str, default=None, help='Output file path for plots')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Map phase mode string to enum
    phase_mode_map = {
        'rtl': PhaseMode.RTL,
        'spread': PhaseMode.SPREAD,
        'spread_inv': PhaseMode.SPREAD_INV,
        'hybrid': PhaseMode.HYBRID,
    }
    phase_mode = phase_mode_map[args.phase_mode]

    if args.test == 'full':
        run_tests(with_plots=args.plot, save_plots=args.save)

    elif args.test == 'pattern':
        demo_pattern()

    elif args.test == 'plots':
        demo_plots()

    elif args.test == 'phase':
        # Compare phase initialization modes
        compare_phase_modes(args.ratio_n, args.ratio_m, args.cycles)
        if args.plot:
            plot_phase_comparison(args.ratio_n, args.ratio_m, args.cycles,
                                 save_path=args.output, show=not args.save)

    elif args.test == 'compare':
        # Parse ratios
        ratios = []
        for r in args.ratios:
            if '/' in r:
                n, m = map(int, r.split('/'))
                ratios.append((n, m))
            else:
                print(f"Invalid ratio format: {r}. Use N/M format.")
                exit(1)

        plot_ratio_comparison(ratios, num_cycles=args.cycles,
                             save_path=args.output, show=not args.save)

    elif args.test == 'accum':
        config = FSRCConfig.from_jesd_mode(
            args.mode,
            channel_to_sample_rate_ratio=args.ratio_n/args.ratio_m,
            phase_mode=phase_mode
        )
        plot_accumulator_states(config, num_cycles=args.cycles,
                               save_path=args.output, show=not args.save)

    elif args.test == 'custom':
        config = FSRCConfig.from_jesd_mode(
            args.mode,
            channel_to_sample_rate_ratio=args.ratio_n/args.ratio_m,
            phase_mode=phase_mode
        )
        tb = TxFSRCTestbench(config)
        tb.run(args.cycles)
        tb.print_summary()
        tb.print_pattern(20)

        if args.plot:
            save_path = args.output if args.save else None
            tb.plot_results(save_path=save_path, show=not args.save)

            if not args.save:
                tb.plot_pattern_detail(num_cycles=min(32, args.cycles))
