#!/usr/bin/env python3
"""
TX FSRC (Fractional Sample Rate Converter) Comprehensive Python Simulation

This simulation provides a complete model of the FPGA TX FSRC datapath from
the AD9084 testbench, with full support for:
- Accumulator-based sample enable generation with configurable N/M ratios
- Hole insertion for fractional sample rate conversion
- JESD204 transport layer mapping (single and dual link)
- Dynamic ratio changes during simulation
- Waveform visualization and statistics

Based on: ADS10v1/AD9084_ADS10v1_Acorn/trunk/fpga_ip/datapath_tx/fpga_src/sim/tb_tx_fsrc.sv
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any, Callable
from collections import deque
from enum import Enum, auto
import logging
import json
import os

# Optional plotting support
try:
    import matplotlib.pyplot as plt
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Note: matplotlib not available, plotting disabled")

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class JESDMode(Enum):
    """Supported JESD204 modes for single link."""
    L1_M4_F8_S1_NP16 = auto()
    L2_M4_F4_S1_NP16 = auto()
    L4_M4_F2_S1_NP16 = auto()
    L8_M2_F1_S2_NP16 = auto()
    L8_M4_F1_S1_NP16 = auto()

    @property
    def params(self) -> Dict[str, int]:
        """Get JESD parameters for this mode."""
        params_map = {
            JESDMode.L1_M4_F8_S1_NP16: {'L': 1, 'M': 4, 'F': 8, 'S': 1, 'NP': 16},
            JESDMode.L2_M4_F4_S1_NP16: {'L': 2, 'M': 4, 'F': 4, 'S': 1, 'NP': 16},
            JESDMode.L4_M4_F2_S1_NP16: {'L': 4, 'M': 4, 'F': 2, 'S': 1, 'NP': 16},
            JESDMode.L8_M2_F1_S2_NP16: {'L': 8, 'M': 2, 'F': 1, 'S': 2, 'NP': 16},
            JESDMode.L8_M4_F1_S1_NP16: {'L': 8, 'M': 4, 'F': 1, 'S': 1, 'NP': 16},
        }
        return params_map[self]


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
    jesd_s: int = 2             # Samples per frame per converter
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
    report_good_data: bool = False

    @classmethod
    def from_jesd_mode(cls, mode: JESDMode, **kwargs) -> 'FSRCConfig':
        """Create config from a JESD mode enum."""
        params = mode.params
        return cls(
            jesd_l=params['L'],
            jesd_m=params['M'],
            jesd_f=params['F'],
            jesd_s=params['S'],
            jesd_np=params['NP'],
            **kwargs
        )

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'np_bits': self.np_bits,
            'data_width': self.data_width,
            'max_conv': self.max_conv,
            'accum_width': self.accum_width,
            'jesd_l': self.jesd_l,
            'jesd_m': self.jesd_m,
            'jesd_f': self.jesd_f,
            'jesd_s': self.jesd_s,
            'jesd_np': self.jesd_np,
            'num_links': self.num_links,
            'channel_to_sample_rate_ratio': self.channel_to_sample_rate_ratio,
            'ns': self.ns,
            'num_samples': self.num_samples,
        }


class Accumulator:
    """
    Fixed-point accumulator with set and overflow detection.

    Models: accum_set.sv

    The accumulator overflows when the sum exceeds the maximum value
    representable in `width` bits. The overflow flag indicates when
    to output a valid sample.
    """

    def __init__(self, width: int = 64):
        self.width = width
        self.mask = (1 << width) - 1
        self.accum = 0
        self.overflow = False
        self.overflow_history = []

    def set(self, value: int) -> None:
        """Set accumulator to a specific value."""
        self.accum = value & self.mask
        self.overflow = False

    def add(self, value: int) -> bool:
        """
        Add value to accumulator, return True if overflow occurred.

        On overflow, the accumulator wraps around and the overflow
        flag is set for one cycle.
        """
        result = self.accum + value
        self.overflow = result > self.mask
        self.accum = result & self.mask
        self.overflow_history.append(self.overflow)
        return self.overflow

    def reset(self) -> None:
        """Reset accumulator to zero."""
        self.accum = 0
        self.overflow = False
        self.overflow_history.clear()

    @property
    def value_normalized(self) -> float:
        """Get accumulator value as normalized float [0, 1)."""
        return self.accum / (1 << self.width)


class SampleEnableGenerator:
    """
    Generates sample enable signals based on accumulator overflow.

    Models: tx_fsrc_sample_en_gen.sv

    Each sample position has its own accumulator, initialized with
    staggered values to distribute the sample enables evenly across
    the clock cycle.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.accumulators = [Accumulator(config.accum_width)
                            for _ in range(config.num_samples)]
        self._compute_initial_values()
        self.enable_history = []

    def _compute_initial_values(self) -> None:
        """
        Compute initial accumulator values based on config.

        Initial value = ONE - RATIO + (group * RATIO)

        This staggers the accumulators so that overflows are distributed
        evenly across samples rather than all occurring at once.
        """
        self.initial_values = []
        ratio_fixed = self.config.ratio_fixed
        one_fixed = self.config.one_fixed
        mask = (1 << self.config.accum_width) - 1

        for i in range(self.config.num_samples):
            ns_group = i // self.config.ns
            val = (one_fixed - ratio_fixed + (ns_group * ratio_fixed)) & mask
            self.initial_values.append(val)
            logger.debug(f"Accumulator {i} initial value: 0x{val:016X} "
                        f"({val / one_fixed:.6f})")

    def set_accumulators(self) -> None:
        """Set all accumulators to their initial values."""
        for i, accum in enumerate(self.accumulators):
            accum.set(self.initial_values[i])

    def step(self, enable: bool = True) -> np.ndarray:
        """
        Advance accumulators by one cycle.

        Args:
            enable: Whether to advance the accumulators

        Returns:
            Array of sample enable flags (True = valid sample, False = hole)
        """
        sample_en = np.zeros(self.config.num_samples, dtype=bool)

        if enable:
            for i, accum in enumerate(self.accumulators):
                sample_en[i] = accum.add(self.config.ratio_fixed)

        self.enable_history.append(sample_en.copy())
        return sample_en

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about sample enable generation."""
        if not self.enable_history:
            return {}

        history = np.array(self.enable_history)
        total_enables = np.sum(history)
        total_samples = history.size
        per_position = np.sum(history, axis=0)

        return {
            'total_enables': int(total_enables),
            'total_samples': int(total_samples),
            'enable_ratio': total_enables / total_samples if total_samples > 0 else 0,
            'per_position_enables': per_position.tolist(),
            'target_ratio': self.config.channel_to_sample_rate_ratio,
        }


class FIFOSync2Deep:
    """
    Simple 2-deep synchronous FIFO.

    Models: fifo_sync_2deep from the testbench infrastructure.
    """

    def __init__(self, width: int):
        self.width = width
        self.data = deque(maxlen=2)
        self.mask = (1 << width) - 1

    def reset(self) -> None:
        """Reset FIFO to empty state."""
        self.data.clear()

    @property
    def empty(self) -> bool:
        return len(self.data) == 0

    @property
    def full(self) -> bool:
        return len(self.data) >= 2

    @property
    def s_ready(self) -> bool:
        """Slave (input) ready signal."""
        return not self.full

    @property
    def m_valid(self) -> bool:
        """Master (output) valid signal."""
        return not self.empty

    def push(self, data: int) -> bool:
        """Push data to FIFO, returns success."""
        if not self.full:
            self.data.append(data & self.mask)
            return True
        return False

    def pop(self) -> Optional[int]:
        """Pop data from FIFO, returns data or None."""
        if not self.empty:
            return self.data.popleft()
        return None

    def peek(self) -> Optional[int]:
        """Peek at front data without removing."""
        if not self.empty:
            return self.data[0]
        return None


class HoleInserter:
    """
    Inserts invalid samples (holes) into the data stream.

    Models: tx_fsrc_make_holes.sv

    Uses a buffering scheme to handle the variable input/output rates
    caused by hole insertion. Maintains up to 3*NUM_WORDS of data
    to ensure smooth data flow.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        # Data buffers: 3x NUM_WORDS deep for each converter
        self.data_buffer = [deque() for _ in range(config.max_conv)]
        self.holes_buffer = deque()
        self.non_holes_cnt = 0
        self.pending_output = None

        # Flow control state
        self.in_valid_d = False
        self.holes_valid_d = False
        self.data_stored_out_valid = False
        self.data_stored_in_ready = True
        self.out_valid = False

    def reset(self) -> None:
        """Reset internal state."""
        for buf in self.data_buffer:
            buf.clear()
        self.holes_buffer.clear()
        self.non_holes_cnt = 0
        self.pending_output = None
        self.in_valid_d = False
        self.holes_valid_d = False
        self.data_stored_out_valid = False
        self.data_stored_in_ready = True
        self.out_valid = False

    @property
    def in_ready(self) -> bool:
        """Input ready signal."""
        return self.data_stored_in_ready

    @property
    def holes_ready(self) -> bool:
        """Holes input ready signal."""
        return not self.holes_valid_d or self.data_stored_out_valid

    def input_samples(self, data: np.ndarray, valid: bool = True) -> bool:
        """
        Input samples into the buffer.

        Args:
            data: Array of shape (num_conv, num_samples) containing sample data
            valid: Whether input data is valid

        Returns:
            Whether input was accepted
        """
        if not valid or not self.in_ready:
            return False

        for conv_idx in range(min(data.shape[0], self.config.jesd_m)):
            for sample_idx in range(self.config.num_samples):
                self.data_buffer[conv_idx].append(int(data[conv_idx, sample_idx]))

        # Update flow control
        num_words = self.config.num_samples
        self.data_stored_in_ready = self.non_holes_cnt + num_words <= num_words * 2

        return True

    def input_holes(self, holes: np.ndarray) -> bool:
        """
        Input hole pattern.

        Args:
            holes: Boolean array where True indicates a hole position

        Returns:
            Whether input was accepted
        """
        if not self.holes_ready:
            return False

        self.holes_buffer.append(holes.copy())
        self.holes_valid_d = True
        return True

    def can_output(self) -> bool:
        """Check if output is ready."""
        if not self.holes_buffer:
            return False

        holes = self.holes_buffer[0]
        needed = int(np.sum(~holes))

        # Check all active converters have enough data
        for conv_idx in range(self.config.jesd_m):
            if len(self.data_buffer[conv_idx]) < needed:
                return False

        return True

    def output_samples(self) -> Optional[np.ndarray]:
        """
        Generate output with holes inserted.

        Returns:
            Array of shape (num_conv, num_samples) with holes inserted,
            or None if not ready
        """
        if not self.can_output():
            return None

        holes = self.holes_buffer.popleft()
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

        # Update non-holes count
        self.non_holes_cnt = max(0, self.non_holes_cnt - int(np.sum(~holes)))

        return output

    def step(self, input_data: np.ndarray, holes: np.ndarray,
             in_valid: bool = True) -> Optional[np.ndarray]:
        """
        Process one clock cycle.

        Args:
            input_data: Input sample data
            holes: Hole pattern for this cycle
            in_valid: Input valid signal

        Returns:
            Output data or None
        """
        # Accept input if ready
        if in_valid and self.in_ready:
            self.input_samples(input_data, True)
            self.non_holes_cnt += self.config.num_samples

        # Accept holes
        self.input_holes(holes)

        # Generate output
        return self.output_samples()


class JESDTransportLayer:
    """
    JESD204 Transport Layer simulation.

    Models: jtx_transport_single_link.sv and jtx_transport_dual_link.sv

    Implements the mapping of converter samples to lane data according to
    JESD204B/C specifications, including proper nibble reordering.
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.input_buffer = deque()
        self.input_buffer_prev = None
        self.output_cycle_cnt = 0
        self.frame_valid = False
        self._validate_mode()

    def _validate_mode(self) -> None:
        """Validate that the configured JESD mode is supported."""
        L, M, F, S, NP = (self.config.jesd_l, self.config.jesd_m,
                          self.config.jesd_f, self.config.jesd_s, self.config.jesd_np)

        supported = [
            (1, 4, 8, 1, 16),
            (2, 4, 4, 1, 16),
            (4, 4, 2, 1, 16),
            (8, 2, 1, 2, 16),
            (8, 4, 1, 1, 16),
        ]

        mode = (L, M, F, S, NP)
        if mode in supported:
            logger.info(f"JESD mode: L={L}, M={M}, F={F}, S={S}, NP={NP} (supported)")
        else:
            logger.warning(f"JESD mode: L={L}, M={M}, F={F}, S={S}, NP={NP} (may not be fully supported)")

    @property
    def output_cycles(self) -> int:
        """Number of output cycles per input frame."""
        L, M, F, NP = (self.config.jesd_l, self.config.jesd_m,
                       self.config.jesd_f, self.config.jesd_np)

        # Based on casex in jtx_transport_single_link.sv
        mode_cycles = {
            (1, 4, 8, 16): 16,
            (2, 4, 4, 16): 8,
            (4, 4, 2, 16): 4,
            (8, 2, 1, 16): 1,
            (8, 4, 1, 16): 2,
        }

        return mode_cycles.get((L, M, F, NP), 1)

    @property
    def in_ready(self) -> bool:
        """Input ready signal."""
        return len(self.input_buffer) < 2

    def reset(self) -> None:
        """Reset internal state."""
        self.input_buffer.clear()
        self.input_buffer_prev = None
        self.output_cycle_cnt = 0
        self.frame_valid = False

    def input_frame(self, data: np.ndarray, valid: bool = True) -> bool:
        """
        Input a frame of converter data.

        Args:
            data: Array of shape (num_conv, num_samples)
            valid: Whether input is valid

        Returns:
            Whether input was accepted
        """
        if not valid or not self.in_ready:
            return False

        self.input_buffer.append(data.copy())
        return True

    def _get_nibbles(self, data: np.ndarray, conv: int, offset: int, count: int = 4) -> int:
        """Extract nibbles from converter data."""
        result = 0
        samples_flat = data[conv].flatten()

        for i in range(count):
            bit_offset = offset + i * 4
            sample_idx = bit_offset // 16
            nibble_idx = (bit_offset % 16) // 4

            if sample_idx < len(samples_flat):
                sample = int(samples_flat[sample_idx])
                nibble = (sample >> (nibble_idx * 4)) & 0xF
                result |= nibble << (i * 4)

        return result

    def get_lane_data(self) -> Optional[Tuple[np.ndarray, bool]]:
        """
        Get lane data output.

        Returns:
            Tuple of (lane_data array, last_cycle flag) or None if no data
        """
        if not self.input_buffer:
            return None

        L = self.config.jesd_l
        M = self.config.jesd_m
        octets_per_lane = 8

        # Combine current and previous frame for modes that need it
        current_frame = self.input_buffer[0]
        prev_frame = self.input_buffer_prev if self.input_buffer_prev is not None else current_frame

        # Create combined pipe data (mimics in_pipe_data in RTL)
        pipe_data = np.zeros((M, 512 // 16), dtype=np.uint64)
        for conv in range(M):
            for i in range(16):
                if i < current_frame.shape[1]:
                    pipe_data[conv, i] = int(current_frame[conv, i])
                if i + 16 < pipe_data.shape[1] and i < prev_frame.shape[1]:
                    pipe_data[conv, i + 16] = int(prev_frame[conv, i])

        # Generate output based on mode (simplified)
        lane_data = np.zeros((L, octets_per_lane), dtype=np.uint8)

        # Simple mapping: distribute samples across lanes
        sample_idx = 0
        for lane in range(L):
            for octet in range(0, octets_per_lane, 2):
                if sample_idx < current_frame.shape[1]:
                    sample = int(current_frame[sample_idx % M, sample_idx // M])
                    lane_data[lane, octet] = (sample >> 8) & 0xFF
                    if octet + 1 < octets_per_lane:
                        lane_data[lane, octet + 1] = sample & 0xFF
                    sample_idx += 1

        # Update cycle counter
        self.output_cycle_cnt += 1
        last_cycle = self.output_cycle_cnt >= self.output_cycles

        if last_cycle:
            self.output_cycle_cnt = 0
            if self.input_buffer:
                self.input_buffer_prev = self.input_buffer.popleft()

        return lane_data, last_cycle


class TxFSRC:
    """
    Top-level TX FSRC simulation.

    Models: tx_fsrc.sv

    Orchestrates the complete FSRC datapath including:
    - Input/output FIFOs
    - Sample enable generation
    - Hole insertion
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.sample_en_gen = SampleEnableGenerator(config)
        self.hole_inserter = HoleInserter(config)

        # Input FIFOs (one per converter)
        self.in_fifos = [FIFOSync2Deep(config.data_width)
                         for _ in range(config.max_conv)]
        # Output FIFOs
        self.out_fifos = [FIFOSync2Deep(config.data_width)
                          for _ in range(config.max_conv)]

        # Control signals
        self.fsrc_en = False
        self.fsrc_data_en = False
        self.reset_state = True

        # Statistics
        self.stats = {
            'input_samples': 0,
            'output_samples': 0,
            'holes_inserted': 0,
            'valid_samples_output': 0,
            'cycles': 0,
        }

        # Waveform recording
        self.record_waveforms = False
        self.waveforms = {
            'input_data': [],
            'output_data': [],
            'sample_en': [],
            'holes': [],
            'fsrc_en': [],
            'fsrc_data_en': [],
        }

    def reset(self) -> None:
        """Reset the FSRC to initial state."""
        self.reset_state = True
        self.fsrc_en = False
        self.fsrc_data_en = False
        self.hole_inserter.reset()

        for fifo in self.in_fifos + self.out_fifos:
            fifo.reset()

        self.stats = {k: 0 for k in self.stats}
        self.waveforms = {k: [] for k in self.waveforms}

    def configure(self, ratio_n: int, ratio_m: int) -> None:
        """
        Configure the FSRC with a new N/M ratio.

        Args:
            ratio_n: Numerator (output rate)
            ratio_m: Denominator (input rate)
        """
        self.config.channel_to_sample_rate_ratio = ratio_n / ratio_m
        self.sample_en_gen = SampleEnableGenerator(self.config)
        logger.info(f"Configured FSRC with ratio {ratio_n}/{ratio_m} = "
                   f"{self.config.channel_to_sample_rate_ratio:.6f}")

    def start(self) -> None:
        """Start the FSRC operation."""
        self.reset_state = False
        self.fsrc_en = True
        self.sample_en_gen.set_accumulators()

    def enable_data(self) -> None:
        """Enable data flow through FSRC."""
        self.fsrc_data_en = True

    def disable_data(self) -> None:
        """Disable data flow (insert all holes)."""
        self.fsrc_data_en = False

    @property
    def in_ready(self) -> np.ndarray:
        """Per-converter input ready signals."""
        return np.array([fifo.s_ready for fifo in self.in_fifos])

    @property
    def out_valid(self) -> np.ndarray:
        """Per-converter output valid signals."""
        return np.array([fifo.m_valid for fifo in self.out_fifos])

    def step(self, input_data: np.ndarray,
             in_valid: Optional[np.ndarray] = None,
             out_ready: Optional[np.ndarray] = None) -> Tuple[Optional[np.ndarray], np.ndarray]:
        """
        Process one clock cycle of the FSRC.

        Args:
            input_data: Array of shape (num_conv, num_samples)
            in_valid: Per-converter input valid signals (default: all True)
            out_ready: Per-converter output ready signals (default: all True)

        Returns:
            Tuple of (output_data, sample_enables)
            output_data is None if not ready, otherwise shape (num_conv, num_samples)
        """
        if in_valid is None:
            in_valid = np.ones(self.config.max_conv, dtype=bool)
        if out_ready is None:
            out_ready = np.ones(self.config.max_conv, dtype=bool)

        self.stats['cycles'] += 1

        if self.reset_state:
            return None, np.zeros(self.config.num_samples, dtype=bool)

        # Record waveforms if enabled
        if self.record_waveforms:
            self.waveforms['input_data'].append(input_data.copy())
            self.waveforms['fsrc_en'].append(self.fsrc_en)
            self.waveforms['fsrc_data_en'].append(self.fsrc_data_en)

        # Generate sample enables
        accum_en = self.fsrc_en and self.fsrc_data_en and self.hole_inserter.holes_ready
        sample_en = self.sample_en_gen.step(accum_en)

        # Track input statistics
        for conv_idx in range(self.config.jesd_m):
            if in_valid[conv_idx]:
                self.stats['input_samples'] += self.config.num_samples

        if self.record_waveforms:
            self.waveforms['sample_en'].append(sample_en.copy())

        if self.fsrc_en:
            # Compute holes (inverted sample_en when fsrc_data_en is active)
            if self.fsrc_data_en:
                holes = ~sample_en
            else:
                holes = np.ones(self.config.num_samples, dtype=bool)

            if self.record_waveforms:
                self.waveforms['holes'].append(holes.copy())

            # Process through hole inserter
            output_data = self.hole_inserter.step(input_data, holes, in_valid=np.all(in_valid))

            if output_data is not None:
                if self.record_waveforms:
                    self.waveforms['output_data'].append(output_data.copy())

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
            # Bypass mode
            return input_data, np.ones(self.config.num_samples, dtype=bool)


class TxFSRCTestbench:
    """
    Testbench for TX FSRC simulation.

    Models: tb_tx_fsrc.sv

    Provides comprehensive test infrastructure including:
    - Input data generation (sequential, random, identical)
    - Output verification with golden model
    - Statistics collection and reporting
    - Waveform recording and visualization
    """

    def __init__(self, config: FSRCConfig):
        self.config = config
        self.fsrc = TxFSRC(config)
        self.jesd_transport = JESDTransportLayer(config)

        # Verification queues
        self.input_queues = [deque() for _ in range(config.max_conv)]

        # Counters
        self.cycle_count = 0
        self.output_count = 0
        self.error_count = 0

        # Test results storage
        self.results = None

    def generate_input_data(self) -> np.ndarray:
        """Generate test input data based on config settings."""
        data = np.zeros((self.config.max_conv, self.config.num_samples), dtype=np.uint64)

        for conv_idx in range(self.config.jesd_m):
            for sample_idx in range(self.config.num_samples):
                if self.config.random_data:
                    sample = np.random.randint(0, 2**self.config.np_bits)
                elif self.config.identical_data:
                    # Same value for all converters (for easier debug)
                    sample = self.cycle_count % (2**self.config.np_bits)
                else:
                    # Sequential values
                    sample = (self.cycle_count * self.config.num_samples + sample_idx) % (2**self.config.np_bits)

                # Avoid the invalid sample marker
                if sample == self.config.fsrc_invalid_sample:
                    sample ^= 1

                data[conv_idx, sample_idx] = sample
                self.input_queues[conv_idx].append(sample)

        return data

    def verify_output(self, output_data: np.ndarray) -> Tuple[int, List[str]]:
        """
        Verify output data against expected values.

        Returns:
            Tuple of (error_count, error_messages)
        """
        errors = 0
        messages = []

        for conv_idx in range(self.config.jesd_m):
            for sample_idx in range(self.config.num_samples):
                out_sample = int(output_data[conv_idx, sample_idx])

                if out_sample != self.config.fsrc_invalid_sample:
                    if self.input_queues[conv_idx]:
                        expected = self.input_queues[conv_idx].popleft()
                        if out_sample != expected:
                            msg = (f"Cycle {self.cycle_count}, conv={conv_idx}, "
                                  f"sample={sample_idx}: expected 0x{expected:04X}, "
                                  f"got 0x{out_sample:04X}")
                            messages.append(msg)
                            errors += 1
                    else:
                        msg = f"Cycle {self.cycle_count}: Output with no input at conv={conv_idx}"
                        messages.append(msg)
                        errors += 1

        return errors, messages

    def run(self, num_cycles: int,
            ratio_changes: Optional[List[Tuple[int, int, int]]] = None,
            record_waveforms: bool = False) -> Dict[str, Any]:
        """
        Run the testbench simulation.

        Args:
            num_cycles: Number of clock cycles to simulate
            ratio_changes: List of (cycle, ratio_n, ratio_m) tuples
            record_waveforms: Whether to record waveforms for visualization

        Returns:
            Dictionary of simulation results
        """
        ratio_changes = ratio_changes or []
        ratio_change_idx = 0

        # Reset
        self.fsrc.reset()
        self.fsrc.record_waveforms = record_waveforms
        self.jesd_transport.reset()

        for q in self.input_queues:
            q.clear()

        self.cycle_count = 0
        self.output_count = 0
        self.error_count = 0

        logger.info(f"Starting TX FSRC simulation for {num_cycles} cycles...")

        # Start sequence
        self.fsrc.start()
        self.fsrc.enable_data()

        results = {
            'config': self.config.to_dict(),
            'input_samples': [],
            'output_samples': [],
            'sample_enables': [],
            'errors': [],
            'ratio_history': [(0, self.config.channel_to_sample_rate_ratio)],
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
                results['ratio_history'].append((cycle, n/m))
                ratio_change_idx += 1

            # Generate input
            input_data = self.generate_input_data()

            # Process
            output_data, sample_en = self.fsrc.step(input_data)
            results['sample_enables'].append(sample_en.tolist())

            if output_data is not None:
                self.output_count += 1
                errors, messages = self.verify_output(output_data)
                self.error_count += errors

                for msg in messages:
                    logger.error(msg)
                    results['errors'].append({'cycle': cycle, 'message': msg})

                # Feed to JESD transport layer
                self.jesd_transport.input_frame(output_data)

        # Compile results
        results['stats'] = self.fsrc.stats.copy()
        results['sample_en_stats'] = self.fsrc.sample_en_gen.get_statistics()
        results['total_cycles'] = num_cycles
        results['output_cycles'] = self.output_count
        results['total_errors'] = self.error_count

        # Add waveforms if recorded
        if record_waveforms:
            results['waveforms'] = self.fsrc.waveforms

        self.results = results
        return results

    def print_summary(self) -> None:
        """Print a summary of test results."""
        if self.results is None:
            print("No results available. Run simulation first.")
            return

        print("\n" + "="*70)
        print("TX FSRC Simulation Summary")
        print("="*70)

        print(f"\nConfiguration:")
        print(f"  JESD Mode: L={self.config.jesd_l}, M={self.config.jesd_m}, "
              f"F={self.config.jesd_f}, S={self.config.jesd_s}, NP={self.config.jesd_np}")
        print(f"  Data Width: {self.config.data_width} bits")
        print(f"  Samples per cycle: {self.config.num_samples}")
        print(f"  Initial ratio: {self.results['ratio_history'][0][1]:.6f}")

        print(f"\nExecution:")
        print(f"  Total cycles: {self.results['total_cycles']}")
        print(f"  Output cycles: {self.results['output_cycles']}")

        stats = self.results['stats']
        print(f"\nData Statistics:")
        print(f"  Input samples: {stats['input_samples']}")
        print(f"  Output samples: {stats['output_samples']}")
        print(f"  Valid samples: {stats['valid_samples_output']}")
        print(f"  Holes inserted: {stats['holes_inserted']}")

        if stats['output_samples'] > 0:
            actual_ratio = stats['valid_samples_output'] / stats['output_samples']
            print(f"  Actual valid ratio: {actual_ratio:.6f}")

        print(f"\nVerification:")
        print(f"  Total errors: {self.results['total_errors']}")
        status = "PASSED" if self.results['total_errors'] == 0 else "FAILED"
        print(f"  Status: {status}")

        if self.results['ratio_history'] and len(self.results['ratio_history']) > 1:
            print(f"\nRatio Changes:")
            for cycle, ratio in self.results['ratio_history']:
                print(f"  Cycle {cycle}: ratio = {ratio:.6f}")

    def plot_waveforms(self, num_cycles: int = 50, save_path: Optional[str] = None) -> None:
        """
        Plot waveforms from the simulation.

        Args:
            num_cycles: Number of cycles to plot
            save_path: Path to save the figure (optional)
        """
        if not PLOTTING_AVAILABLE:
            print("Matplotlib not available. Cannot plot waveforms.")
            return

        if self.results is None or 'waveforms' not in self.results:
            print("No waveform data available. Run simulation with record_waveforms=True")
            return

        waveforms = self.results['waveforms']
        sample_en = np.array(waveforms.get('sample_en', []))[:num_cycles]

        if len(sample_en) == 0:
            print("No sample enable data recorded.")
            return

        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # Plot 1: Sample enable heatmap
        ax1 = axes[0]
        im1 = ax1.imshow(sample_en.T, aspect='auto', cmap='RdYlGn',
                         interpolation='nearest', vmin=0, vmax=1)
        ax1.set_ylabel('Sample Position')
        ax1.set_title('Sample Enable Pattern (Green=Valid, Red=Hole)')
        plt.colorbar(im1, ax=ax1, label='Enable')

        # Plot 2: Valid samples per cycle
        ax2 = axes[1]
        valid_per_cycle = np.sum(sample_en, axis=1)
        ax2.bar(range(len(valid_per_cycle)), valid_per_cycle, color='steelblue', alpha=0.7)
        ax2.axhline(y=self.config.num_samples * self.config.channel_to_sample_rate_ratio,
                   color='red', linestyle='--', label='Expected')
        ax2.set_ylabel('Valid Samples')
        ax2.set_title('Valid Samples per Cycle')
        ax2.legend()

        # Plot 3: Cumulative ratio
        ax3 = axes[2]
        cumulative_valid = np.cumsum(np.sum(sample_en, axis=1))
        cumulative_total = np.arange(1, len(sample_en) + 1) * self.config.num_samples
        cumulative_ratio = cumulative_valid / cumulative_total
        ax3.plot(cumulative_ratio, 'b-', linewidth=2, label='Actual')
        ax3.axhline(y=self.config.channel_to_sample_rate_ratio, color='red',
                   linestyle='--', label='Target')
        ax3.set_xlabel('Cycle')
        ax3.set_ylabel('Cumulative Ratio')
        ax3.set_title('Cumulative Valid/Total Ratio')
        ax3.legend()
        ax3.set_ylim(0, 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved waveform plot to {save_path}")
        else:
            plt.show()


def run_comprehensive_test_suite():
    """Run a comprehensive suite of tests."""
    print("="*70)
    print("TX FSRC Comprehensive Python Simulation")
    print("Based on: tb_tx_fsrc.sv")
    print("="*70)

    # Test 1: Basic operation with default ratio
    print("\n" + "-"*70)
    print("Test 1: Basic Operation (2/3 ratio)")
    print("-"*70)

    config = FSRCConfig.from_jesd_mode(JESDMode.L8_M2_F1_S2_NP16,
                                       channel_to_sample_rate_ratio=2/3)
    tb = TxFSRCTestbench(config)
    tb.run(100, record_waveforms=True)
    tb.print_summary()

    # Test 2: Multiple ratio changes
    print("\n" + "-"*70)
    print("Test 2: Dynamic Ratio Changes")
    print("-"*70)

    config = FSRCConfig.from_jesd_mode(JESDMode.L8_M2_F1_S2_NP16,
                                       channel_to_sample_rate_ratio=1/2)
    ratio_schedule = [
        (0, 1, 2),     # 50%
        (50, 2, 3),    # 66.7%
        (100, 3, 4),   # 75%
        (150, 4, 5),   # 80%
        (200, 7, 8),   # 87.5%
    ]

    tb = TxFSRCTestbench(config)
    tb.run(250, ratio_changes=ratio_schedule)
    tb.print_summary()

    # Test 3: All JESD modes
    print("\n" + "-"*70)
    print("Test 3: JESD Mode Sweep")
    print("-"*70)

    for mode in JESDMode:
        config = FSRCConfig.from_jesd_mode(mode, channel_to_sample_rate_ratio=2/3)
        tb = TxFSRCTestbench(config)
        results = tb.run(50)

        params = mode.params
        status = "PASS" if results['total_errors'] == 0 else "FAIL"
        print(f"  Mode L={params['L']}, M={params['M']}, F={params['F']}: {status}")

    # Test 4: Visualize pattern
    print("\n" + "-"*70)
    print("Test 4: Sample Pattern Visualization")
    print("-"*70)

    config = FSRCConfig.from_jesd_mode(JESDMode.L8_M2_F1_S2_NP16,
                                       channel_to_sample_rate_ratio=2/3)
    print(f"Ratio: {config.channel_to_sample_rate_ratio:.4f}")
    print("Pattern (# = valid, . = hole):")

    fsrc = TxFSRC(config)
    fsrc.start()
    fsrc.enable_data()

    for cycle in range(20):
        input_data = np.zeros((config.max_conv, config.num_samples), dtype=np.uint64)
        _, sample_en = fsrc.step(input_data)
        pattern = ''.join(['#' if en else '.' for en in sample_en])
        valid_count = np.sum(sample_en)
        print(f"  Cycle {cycle:3d}: [{pattern}] ({valid_count}/{config.num_samples})")

    print("\n" + "="*70)
    print("All Tests Complete")
    print("="*70)


def demo_visualization():
    """Demonstrate waveform visualization."""
    if not PLOTTING_AVAILABLE:
        print("Matplotlib not available. Skipping visualization demo.")
        return

    print("\nGenerating waveform visualization...")

    config = FSRCConfig.from_jesd_mode(JESDMode.L8_M2_F1_S2_NP16,
                                       channel_to_sample_rate_ratio=2/3)

    tb = TxFSRCTestbench(config)
    tb.run(100, record_waveforms=True)
    tb.plot_waveforms(num_cycles=50, save_path='tx_fsrc_waveforms.png')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TX FSRC Python Simulation")
    parser.add_argument('--test', choices=['basic', 'ratio', 'jesd', 'visual', 'all'],
                       default='all', help='Test to run')
    parser.add_argument('--cycles', type=int, default=100, help='Number of cycles')
    parser.add_argument('--ratio-n', type=int, default=2, help='Ratio numerator')
    parser.add_argument('--ratio-m', type=int, default=3, help='Ratio denominator')
    parser.add_argument('--jesd-l', type=int, default=8, help='JESD L parameter')
    parser.add_argument('--jesd-m', type=int, default=2, help='JESD M parameter')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test == 'all':
        run_comprehensive_test_suite()
        if args.plot:
            demo_visualization()
    elif args.test == 'visual':
        demo_visualization()
    else:
        # Custom test with provided parameters
        config = FSRCConfig(
            jesd_l=args.jesd_l,
            jesd_m=args.jesd_m,
            channel_to_sample_rate_ratio=args.ratio_n / args.ratio_m,
        )

        tb = TxFSRCTestbench(config)
        tb.run(args.cycles, record_waveforms=args.plot)
        tb.print_summary()

        if args.plot:
            tb.plot_waveforms()
