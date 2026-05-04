# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys, time

import adi
import matplotlib.pyplot as plt
import matplotlib.widgets as mw
import numpy as np

plt.style.use('dark_background')
plt.rcParams.update({
    'axes.grid':        True,
    'grid.color':       '#0a3a0a',
    'grid.linestyle':   ':',
    'grid.linewidth':   0.6,
    'axes.edgecolor':   '#00cc66',
    'axes.linewidth':   1.0,
    'figure.facecolor': '#0c0c0c',
    'axes.facecolor':   '#000000',
    'lines.linewidth':  1.1,
    'axes.prop_cycle':  plt.cycler('color', ['#00ff88', '#ffaa00', '#ff66ff', '#44ddff']),
})
UPPER_THRESHOLD_COLOR = '#ff5577'
LOWER_THRESHOLD_COLOR = "#0820ff"
TRIGGER_COLOR   = '#ffff66'
BTN_COLOR       = '#1a1a1a'
BTN_HOVER       = '#003322'
TAB_ACTIVE      = '#00aaff'
TAB_INACTIVE    = '#1a1a1a'
TAB_LBL_ACTIVE  = '#000000'
TAB_LBL_INACTIVE = '#888888'

uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print(f"uri: {uri}")

adcs = [
    adi.hmcad15xx(uri=uri, device_name="axi_adc1_hmcad15xx"),
    adi.hmcad15xx(uri=uri, device_name="axi_adc2_hmcad15xx")
]

triggers = [
    adi.trigger_detection(uri, adi.trigger_detection.BASE_CHANNEL_0),
    adi.trigger_detection(uri, adi.trigger_detection.BASE_CHANNEL_1)
]

### config adcs ###
adcs[0].rx_enabled_channels = [0]
adcs[0].channel[0].input_select=  "IP4_IN4"
adcs[0].channel[1].input_select = "IP4_IN4"
adcs[0].channel[2].input_select = "IP4_IN4"
adcs[0].channel[3].input_select = "IP4_IN4"

adcs[1].rx_enabled_channels = [0]
adcs[1].channel[0].input_select=  "IP1_IN1"
adcs[1].channel[1].input_select = "IP1_IN1"
adcs[1].channel[2].input_select = "IP1_IN1"
adcs[1].channel[3].input_select = "IP1_IN1"

for adc in adcs:
    adc.hmcad15xx_register_write(0x26, 0x5a00)  # custom pattern value
    adc.hmcad15xx_register_write(0x25, 0x00)    # pattern disabled
    adc.hmcad15xx_register_write(0x46, 0x0)     # raw ADC samples (not 2's complement)

### Defaults / state ###
DEFAULT_PARAMS = {
    'lower_threshold':        130,
    'upper_threshold':        150,
    'num_context_frames':     50,
    'num_frames_per_trigger': 1024,
    'trigger_mode':           0,
    'single_trigger':         True,
}
ENTRY_TYPES  = ['bypass', 'single_trigger']
PARAM_FIELDS = ['lower_threshold', 'upper_threshold',
                'num_context_frames', 'num_frames_per_trigger', 'trigger_mode']
PARAM_LABELS = {
    'lower_threshold':        'lower',
    'upper_threshold':        'upper',
    'num_context_frames':     'ctx',
    'num_frames_per_trigger': 'frames',
    'trigger_mode':           'mode',
}

state = {
    'data':    {i + 1: {} for i in range(len(adcs))},
    'timeout': 5.0,
}

for trig in triggers:
    for k, v in DEFAULT_PARAMS.items():
        setattr(trig, k, v)

### Capture helpers ###
def capture_bypass(idx):
    adc, trig = adcs[idx], triggers[idx]
    trig.trigger_enable = False
    adc.rx_buffer_size = trig.compute_rx_buffer_size()
    try:
        return np.asarray(adc.rx())
    finally:
        adc.rx_destroy_buffer()

def capture_single(idx):
    adc, trig = adcs[idx], triggers[idx]
    trig.trigger_enable = True
    adc.rx_buffer_size = trig.compute_rx_buffer_size()
    adc._rx_init_channels()
    time.sleep(0.05)
    trig.arm()
    try:
        ok = trig.wait_for_trigger(timeout=state['timeout'])
        if not ok:
            print(f"ADC {idx+1}: TRIGGER TIMEOUT after {state['timeout']}s")
            trig.disarm()
            return None
        return np.asarray(adc.rx())
    finally:
        adc.rx_destroy_buffer()
        trig.trigger_enable = False

def capture_threshold_test(idx, direction):
    """Use HMCAD15xx custom-pattern mode to drive a known transition."""
    adc, trig = adcs[idx], triggers[idx]
    lo, hi = trig.lower_threshold, trig.upper_threshold
    safe = (lo + hi) // 2                                          # midpoint of safe zone
    trigger_val = (hi + 255) // 2 if direction == 'upper' else lo // 2  # halfway from threshold to rail
    safe_reg, trig_reg = (safe << 8) & 0xFFFF, (trigger_val << 8) & 0xFFFF
    print(f"ADC {idx+1} {direction}-test: safe={safe}, fire={trigger_val} (lo={lo}, hi={hi})")

    adc.hmcad15xx_register_write(0x26, safe_reg)
    adc.hmcad15xx_register_write(0x25, 0x10)        # enable single custom pattern

    trig.trigger_enable = True
    adc.rx_buffer_size = trig.compute_rx_buffer_size()
    adc._rx_init_channels()
    time.sleep(2) # FIFO fills with safe pattern
    trig.arm()
    adc.hmcad15xx_register_write(0x26, trig_reg)     # flip to violating value -> trigger

    try:
        ok = trig.wait_for_trigger(timeout=state['timeout'])
        if not ok:
            print(f"ADC {idx+1}: {direction}-test TIMEOUT")
            trig.disarm()
            return None
        return np.asarray(adc.rx())
    finally:
        adc.rx_destroy_buffer()
        trig.trigger_enable = False
        adc.hmcad15xx_register_write(0x25, 0x00)     # back to live signal

# Initial bypass capture so plots aren't empty when the figure opens
for i in range(len(adcs)):
    state['data'][i + 1]['bypass'] = capture_bypass(i)

state['current_adc'] = 1

### Figure ###
fig = plt.figure(figsize=(14, 10))

# Plot region (single column — only the active ADC's plots are shown)
plot_axes = {}
plot_top, plot_bottom = 0.84, 0.06
plot_left, plot_right = 0.07, 0.97
n_rows  = len(ENTRY_TYPES)
cell_h  = (plot_top - plot_bottom) / n_rows
pad_y   = 0.04

share_x = share_y = None
for row, entry in enumerate(ENTRY_TYPES):
    y = plot_bottom + (n_rows - 1 - row) * cell_h + pad_y
    h = cell_h - 2 * pad_y
    ax = fig.add_axes([plot_left, y, plot_right - plot_left, h],
                      sharex=share_x, sharey=share_y)
    share_x = share_x or ax
    share_y = share_y or ax
    plot_axes[entry] = ax

def redraw():
    adc_id = state['current_adc']
    trig = triggers[adc_id - 1]
    trigger_idx = trig.num_context_frames * trig.FRAME_SIZE_SAMPLES
    for row, entry in enumerate(ENTRY_TYPES):
        ax = plot_axes[entry]
        ax.clear()
        d = state['data'][adc_id]
        if entry not in d:
            ax.text(0.5, 0.5, 'no data', transform=ax.transAxes,
                    ha='center', va='center', color='gray', fontsize=14)
        elif d[entry] is None:
            ax.text(0.5, 0.5, 'TIMEOUT', transform=ax.transAxes,
                    ha='center', va='center', color='red',
                    fontsize=22, fontweight='bold')
        else:
            code = d[entry].view(np.uint8)[0::2]
            ax.plot(code, color=f'C{row}')
        ax.set_ylim(-5, 260)
        ax.axhline(trig.lower_threshold, color=UPPER_THRESHOLD_COLOR, linestyle='--', alpha=0.7)
        ax.axhline(trig.upper_threshold, color=LOWER_THRESHOLD_COLOR, linestyle='--', alpha=0.7)
        if entry != 'bypass':
            ax.axvline(trigger_idx, color=TRIGGER_COLOR, linestyle='--', alpha=0.8,
                       label=f"expected trigger @ {trigger_idx}")
            ax.legend(loc='upper right', fontsize=8)
        ax.set_ylabel(f"{entry}\n(ADC Code)")
        if row == 0:
            ax.set_title(f"ADC {adc_id}")
        if row == n_rows - 1:
            ax.set_xlabel("Samples")
    fig.canvas.draw_idle()

### Widgets ###
widgets_keep = []
textboxes    = {}     # textboxes[field] -> TextBox  (single shared row)
tab_buttons  = {}     # tab_buttons[adc_id] -> Button

def add_textbox(rect, label, initial):
    ax = fig.add_axes(rect)
    tb = mw.TextBox(ax, label, initial=str(initial), color='#1a1a1a', hovercolor='#222a22')
    tb.text_disp.set_color('#cccccc')
    tb.label.set_color('#cccccc')
    widgets_keep.append(tb)
    return tb

def add_button(rect, label):
    ax = fig.add_axes(rect)
    btn = mw.Button(ax, label, color=BTN_COLOR, hovercolor=BTN_HOVER)
    btn.label.set_color('#cccccc')
    widgets_keep.append(btn)
    return btn

def load_textboxes_from(adc_id):
    """Sync textbox values from triggers[adc_id - 1]."""
    trig = triggers[adc_id - 1]
    for field in PARAM_FIELDS:
        textboxes[field].set_val(str(getattr(trig, field)))

def select_adc(adc_id):
    state['current_adc'] = adc_id
    load_textboxes_from(adc_id)
    for aid, btn in tab_buttons.items():
        active = (aid == adc_id)
        btn.ax.set_facecolor(TAB_ACTIVE if active else TAB_INACTIVE)
        btn.label.set_color(TAB_LBL_ACTIVE if active else TAB_LBL_INACTIVE)
        btn.label.set_fontweight('bold' if active else 'normal')
        btn.color = TAB_ACTIVE if active else TAB_INACTIVE
        btn.hovercolor = '#33bbff' if active else BTN_HOVER
    redraw()

def apply_params():
    idx = state['current_adc'] - 1
    trig = triggers[idx]
    try:
        trig.lower_threshold        = int(textboxes['lower_threshold'].text)
        trig.upper_threshold        = int(textboxes['upper_threshold'].text)
        trig.num_context_frames     = int(textboxes['num_context_frames'].text)
        trig.num_frames_per_trigger = int(textboxes['num_frames_per_trigger'].text)
        trig.trigger_mode           = int(textboxes['trigger_mode'].text)
    except ValueError as e:
        print(f"ADC {idx+1}: invalid value -- {e}")
        return False
    return True

def on_full(_=None):
    if not apply_params(): return
    idx = state['current_adc'] - 1
    adc_id = idx + 1
    state['data'][adc_id]['bypass']         = capture_bypass(idx)
    state['data'][adc_id]['single_trigger'] = capture_single(idx)
    redraw()

def on_bypass(_=None):
    if not apply_params(): return
    idx = state['current_adc'] - 1
    adc_id = idx + 1
    state['data'][adc_id]['bypass'] = capture_bypass(idx)
    redraw()

def on_test_upper(_=None):
    if not apply_params(): return
    idx = state['current_adc'] - 1
    state['data'][idx + 1]['single_trigger'] = capture_threshold_test(idx, 'upper')
    redraw()

def on_test_lower(_=None):
    if not apply_params(): return
    idx = state['current_adc'] - 1
    state['data'][idx + 1]['single_trigger'] = capture_threshold_test(idx, 'lower')
    redraw()

# === Top control strip ===

# Row A (y=0.93): tabs + parameter textboxes + checkbox
tab_y, tab_h, tab_w = 0.93, 0.035, 0.05
for i in range(len(adcs)):
    adc_id = i + 1
    btn = add_button([0.02 + i * (tab_w + 0.005), tab_y, tab_w, tab_h], f'ADC{adc_id}')
    btn.on_clicked(lambda e, aid=adc_id: select_adc(aid))
    tab_buttons[adc_id] = btn

tb_h, tb_w, tb_gap = 0.030, 0.06, 0.05
x = 0.18
for field in PARAM_FIELDS:
    tb = add_textbox([x, tab_y + 0.002, tb_w, tb_h], PARAM_LABELS[field], DEFAULT_PARAMS[field])
    textboxes[field] = tb
    x += tb_w + tb_gap

# Row B (y=0.87): action buttons + global timeout (right end)
act_y, act_h = 0.87, 0.035
btn_full     = add_button([0.04, act_y, 0.13, act_h], 'Bypass + Single')
btn_bypass   = add_button([0.18, act_y, 0.13, act_h], 'Bypass Only')
btn_test_up  = add_button([0.32, act_y, 0.13, act_h], 'Test Upper Thr')
btn_test_lo  = add_button([0.46, act_y, 0.13, act_h], 'Test Lower Thr')
btn_full.on_clicked(on_full)
btn_bypass.on_clicked(on_bypass)
btn_test_up.on_clicked(on_test_upper)
btn_test_lo.on_clicked(on_test_lower)

def on_timeout_submit(text):
    try:
        state['timeout'] = float(text)
        print(f"trigger timeout = {state['timeout']}s")
    except ValueError:
        print(f"invalid timeout: {text!r}")

timeout_tb = add_textbox([0.86, act_y, 0.08, act_h], 'timeout (s)', state['timeout'])
timeout_tb.on_submit(on_timeout_submit)

# Highlight initial tab + initial render
select_adc(state['current_adc'])
plt.show()
