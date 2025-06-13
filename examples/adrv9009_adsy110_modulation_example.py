"""
Author: Eliza Balas
Date: 2025-05-30
Description: This example demonstrates how to create a UDP server that receives data from the ADSY1100 board and displays it in a Tkinter GUI.
             This example is designed to work with the ADSY1100 board and adrv9009-zu11eg.
Version: 1.0
"""
import time
import numpy as np
import adi
import socket
import threading
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import iio
import paramiko
from scipy import signal
from matplotlib.ticker import MultipleLocator
import keyboard
import commpy.utilities as util
import komm
import scipy.io

# USER CONFIGURATION
ffsom_ip = "192.168.2.1" # ADSY1100 board ip address
talise_ip = "192.168.10.10" # ADRV9009-zu11eg board ip address
nic_card_mac_address = "b8:3f:d2:2a:0b:f0" # NIC card MAC address for port 0
path_to_vu11p_bin = "/boot/images/vu11p.bin"
path_to_vu11p_dtbo = "/boot/images/vu11p.dtbo"
ffsom_board_username = "root"
ffsom_board_password = "root"
xlim = (0, 2048 - 1) # change the X-axis limits as needed
ylim = (-8e3, 8e3) # change the Y-axis limits as needed

# USER SHOULD NOT CHANGE
ffsom_uri = "ip:" + ffsom_ip
talise_uri = "ip:" + talise_ip
fs = 245760000  # samples per second (sps) for the AD9084 / channel
udp_packet_samples_per_ch = 1024 # samples per channel per UDP packet
udp_packet_max_size = 9000 # bytes; jumbo packets

# List of channel names
channel_control = [
    {"name": "voltage0_i", "status": "Enabled"},
    {"name": "voltage0_q", "status": "Enabled"},
    {"name": "voltage1_i", "status": "Disabled"},
    {"name": "voltage1_q", "status": "Disabled"}
]

# Map channel names to their devmem addresses
devmem_map = {
    "voltage0_i": "0x881B0400",
    "voltage0_q": "0x881B0440",
    "voltage1_i": "0x881B0480",
    "voltage1_q": "0x881B04C0",
}

def mac_to_hex(mac_str):
    # Remove colons and convert to integer
    mac_int = int(mac_str.replace(":", ""), 16)
    # Format as hex string (no leading zeros except for '0x')
    return hex(mac_int)

print("\n" + "*" * 40)
print("      -- Setting up ad9084 chip --")
print("*" * 40 + "\n")

# Configure the ffsom board: (make sure # pip install paramiko)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(ffsom_ip, username=ffsom_board_username, password=ffsom_board_password)
print(f"Run cmd: /boot/selmap_dtbo.sh -b {path_to_vu11p_bin}  -d {path_to_vu11p_dtbo}")
stdin, stdout, stderr = ssh.exec_command(f"/boot/selmap_dtbo.sh -b {path_to_vu11p_bin}  -d {path_to_vu11p_dtbo}")
stdout_str = stdout.read().decode()
stderr_str = stderr.read().decode()
print(stdout_str)
print(stderr_str)
# Only wait if there was no "Operation not permitted" error
if "Operation not permitted" not in stderr_str:
    time.sleep(120)  # Waits for 60 seconds (1 minute)
stdin, stdout, stderr = ssh.exec_command(f"ip addr add 192.168.0.69/24 dev eth1")
print(stdout.read().decode())
print(stderr.read().decode())
print(f"Run cmd: ip addr add 192.168.0.69/24 dev eth1")
stdin, stdout, stderr = ssh.exec_command(f"ip link set eth1 up")
print(stdout.read().decode())
print(stderr.read().decode())
print(f"Run cmd: ip link set eth1 up")
stdin, stdout, stderr = ssh.exec_command(f"systemctl restart iiod")
print(stdout.read().decode())
print(stderr.read().decode())
print(f"Run cmd: systemctl restart iiod")
stdin, stdout, stderr = ssh.exec_command(f"echo {mac_to_hex(nic_card_mac_address)} > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/eth_dest_mac")
print(stdout.read().decode())
print(stderr.read().decode())
print(f"Run cmd: echo {mac_to_hex(nic_card_mac_address)} > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/eth_dest_mac")
stdin, stdout, stderr = ssh.exec_command(f"echo {udp_packet_samples_per_ch} > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/sample_count_per_ch")
print(stdout.read().decode())
print(stderr.read().decode())
print(f"Run cmd: echo {udp_packet_samples_per_ch} > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/sample_count_per_ch")

for channel in channel_control:
    name = channel["name"]
    status = channel["status"]
    if name in devmem_map:
        addr = devmem_map[name]
        if status == "Enabled":
            stdin, stdout, stderr = ssh.exec_command(f"busybox devmem {addr} 32 0x00000051")
            print(stdout.read().decode())
            print(stderr.read().decode())
            print(f"Activated {name}")
        else:
            stdin, stdout, stderr = ssh.exec_command(f"busybox devmem {addr} 32 0x00000050")
            print(stdout.read().decode())
            print(stderr.read().decode())
            print(f"Deactivated {name}")
ssh.close()

# Initialize packet_count
packet_count = 0

dev = adi.ad9084(ffsom_uri)

print("CHIP Version:", dev.chip_version)
print("API  Version:", dev.api_version)

print("TX SYNC START AVAILABLE:", dev.tx_sync_start_available)
print("RX SYNC START AVAILABLE:", dev.rx_sync_start_available)

# Set NCOs
dev.rx_channel_nco_frequencies = [0] * 4

dev.rx_main_nco_frequencies = [2400000000] * 4

dev.rx_enabled_channels = [0, 1]
dev.rx_nyquist_zone = ["odd"] * 4

ctx = dev._ctrl.ctx

dev = ctx.find_device("axi-ad9084-rx-hpc") #ffsom board

# Find all available channels for the device and populate the channels list
channels = [channel for channel in dev.channels if channel]

# Extract the channel names (IDs) and print them in the desired format
channel_names = [channel.id for channel in channels]
print(f"Available channels: {channel_names}")

# Create a Tkinter window
root = tk.Tk()
root.title("IMS Demo - AD9084 UDP Server Plot 100G NIC")

# Create a frame for the plot
plot_frame = tk.Frame(root)
plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a frame for the control panel
control_frame = tk.Frame(root)
control_frame.pack(side=tk.RIGHT, fill=tk.Y)

# Create a window with 5 subplots
fig = plt.figure(figsize=(12, 7))
axs = [
    plt.subplot2grid((3, 2), (0, 0)),  # voltage0_i
    plt.subplot2grid((3, 2), (0, 1)),  # voltage0_q
    plt.subplot2grid((3, 2), (1, 0)),  # voltage1_i
    plt.subplot2grid((3, 2), (1, 1)),  # voltage1_q
    plt.subplot2grid((3, 2), (2, 0), colspan=2)  # PSD, spans both columns
]
plt.subplots_adjust(hspace=0.6, wspace=0.3)

for ax in axs[:4]:
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

# Filter channel names that start with "voltage" and remove duplicates
voltage_channels = list(set(name for name in channel_names if name.startswith("voltage")))

# Dictionary to store the state of each checkbox
checkbox_states = {}

# Add a button to trigger new samples
def trigger_new_samples():
    global data_buffers, lines
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ffsom_ip, username=ffsom_board_username, password=ffsom_board_password)
    stdin, stdout, stderr = ssh.exec_command(
        "echo 1 > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/start_app"
    )
    ssh.close()
    # Clear data buffers and update plot
    if 'data_buffers' in globals() and 'lines' in globals():
        for i in range(len(data_buffers)):
            data_buffers[i] = np.zeros_like(data_buffers[i])
            lines[i].set_ydata(data_buffers[i])
        canvas.draw()

# Create a button in the control panel to trigger new samples
trigger_button = tk.Button(control_frame, text="Trigger New Samples", command=trigger_new_samples)
trigger_button.pack(pady=10)

# Iterate through the channel_control list to create checkboxes in the same order
for channel in channel_control:
    name = channel["name"]
    checkbox_states[name] = tk.BooleanVar(value=(channel["status"] == "Enabled"))  # Set initial state based on status
    checkbox = tk.Checkbutton(
        control_frame,
        text=f"Enable {name}",
        variable=checkbox_states[name]  # Bind the checkbox to its BooleanVar
    )
    checkbox.pack(anchor=tk.W)

# Iterate through the channel_control list and enable checkboxes for "Enabled" channels
for channel in channel_control:
    name = channel["name"]
    status = channel["status"]
    if name in checkbox_states:  # Check if the checkbox exists for this channel
        checkbox_states[name].set(status == "Enabled")  # Enable the checkbox if the status is "Enabled"
    else:
        print(f"Channel {name} not found in checkbox_states")

def update_subplots(new_data_matrix=None):
    global axs, lines, fig, canvas, data_buffers

    all_channels = [channel["name"] for channel in channel_control]
    num_channels = len(all_channels)

    # Initialize data_buffers and lines if not already done
    if 'data_buffers' not in globals() or len(data_buffers) != num_channels:
        buffer_len = max(udp_packet_samples_per_ch, xlim[1] + 1)
        data_buffers = [np.zeros(buffer_len) for _ in range(num_channels)]
        lines = [axs[i].plot(data_buffers[i])[0] for i in range(num_channels)]
        # Set titles for the 4 voltage subplots
        for i, ax in enumerate(axs[:4]):
            ax.set_title(f'{all_channels[i]}', fontsize=10)
        # Add a line for the PSD plot
        psd_line, = axs[-1].semilogy([], [])
        lines.append(psd_line)
        canvas.draw()

    if new_data_matrix is None:
        return

    # Map enabled channel indices in channel_control to new_data_matrix rows
    enabled_indices = [i for i, channel in enumerate(channel_control) if channel["status"] == "Enabled"]
    data_row = 0
    for i, channel in enumerate(channel_control):
        if channel["status"] == "Enabled":
            if data_row < new_data_matrix.shape[0]:
                new_data_inc = new_data_matrix[data_row, :]
                data_buffers[i] = np.roll(data_buffers[i], -len(new_data_inc))
                data_buffers[i][-len(new_data_inc):] = new_data_inc
                lines[i].set_ydata(data_buffers[i])
                data_row += 1
            else:
                lines[i].set_ydata([np.nan] * len(data_buffers[i]))
        else:
            lines[i].set_ydata([np.nan] * len(data_buffers[i]))

    # --- Periodogram (PSD) plot for the first enabled channel ---
    if enabled_indices:
        idx_i = next((i for i, ch in enumerate(channel_control) if ch["name"] == "voltage0_i" and ch["status"] == "Enabled"), None)
        idx_q = next((i for i, ch in enumerate(channel_control) if ch["name"] == "voltage0_q" and ch["status"] == "Enabled"), None)
        if idx_i is not None and idx_q is not None:
            y_complex = data_buffers[idx_i] + 1j * data_buffers[idx_q]
            f, Pxx_den = signal.periodogram(y_complex, fs, return_onesided=False)
            f_mhz = f / 1e6
            lines[-1].set_data(f_mhz, Pxx_den)
            axs[-1].set_xlim(-40, 40)
            axs[-1].set_ylim([1e-7, 1e5])
            axs[-1].set_title(f'Periodogram of voltage0 (i and q channels)', fontsize=10)
            axs[-1].set_ylabel("PSD [V**2/Hz]")
            axs[-1].set_xlabel("frequency [MHz]")
            axs[-1].xaxis.set_major_locator(MultipleLocator(1))
        else:
            lines[-1].set_data([], [])
            axs[-1].set_xlim(-40, 40)
            axs[-1].set_ylim([1e-7, 1e5])
            axs[-1].set_ylabel("PSD [V**2/Hz]")
            axs[-1].set_xlabel("frequency [MHz]")

    canvas.draw()

# Call update_subplots whenever the checkbox states change
def handle_checkbox_change():
    global udp_packet_samples_per_ch  # Add this line to modify the global variable

    # Track which channels actually changed status
    status_changed = {}

    # Count enabled channels
    enabled_count = 0

    for channel in channel_control:
        name = channel["name"]
        if name in checkbox_states:
            new_status = "Enabled" if checkbox_states[name].get() else "Disabled"
            if channel["status"] != new_status:
                status_changed[name] = new_status
            channel["status"] = new_status
            if new_status == "Enabled":
                enabled_count += 1

    # Set udp_packet_samples_per_ch based on enabled channels
    if enabled_count == 1:
        udp_packet_samples_per_ch = 4096
    elif enabled_count == 2:
        udp_packet_samples_per_ch = 2048
    elif enabled_count == 3:
        udp_packet_samples_per_ch = 1344
    elif enabled_count == 4:
        udp_packet_samples_per_ch = 1024

    update_subplots()

    # Only send SSH commands if any status changed
    if not status_changed:
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ffsom_ip, username=ffsom_board_username, password=ffsom_board_password)

    for name, new_status in status_changed.items():
        if name in devmem_map:
            addr = devmem_map[name]
            if new_status == "Enabled":
                stdin, stdout, stderr = ssh.exec_command(f"busybox devmem {addr} 32 0x00000051")
                print(stdout.read().decode())
                print(stderr.read().decode())
                print(f"Activated {name}")
            else:
                stdin, stdout, stderr = ssh.exec_command(f"busybox devmem {addr} 32 0x00000050")
                print(stdout.read().decode())
                print(stderr.read().decode())
                print(f"Deactivated {name}")

    # Update sample count on the board
    stdin, stdout, stderr = ssh.exec_command(
        f"echo {udp_packet_samples_per_ch} > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/sample_count_per_ch"
    )
    print(stdout.read().decode())
    print(stderr.read().decode())
    print(f"Run cmd: echo {udp_packet_samples_per_ch} > /sys/bus/auxiliary/devices/mqnic.app_12340001.0/sample_count_per_ch")

    ssh.close()

# Adjust layout to prevent overlap and ensure titles are visible
plt.tight_layout()

# Embed the plot in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def htons(x):
    return ((x & 0x00ff) << 8) | ((x & 0xff00) >> 8)

def convert_buffer_to_network_order(buffer):
    # Ensure the buffer length is a multiple of 2
    if len(buffer) % 2 != 0:
        raise ValueError("Buffer length must be a multiple of 2")

    network_order_buffer = bytearray(len(buffer))

    for i in range(0, len(buffer), 2):
        # Extract two bytes from the buffer
        two_bytes = (buffer[i] << 8) | buffer[i + 1]

        # Convert to network byte order
        network_order_value = htons(two_bytes)

        # Store the converted value back into the network order buffer
        network_order_buffer[i] = (network_order_value >> 8) & 0xff
        network_order_buffer[i + 1] = network_order_value & 0xff

    return network_order_buffer

def handle_client(server_socket):
    global packet_count
    try:
        # Update the channel statuses based on checkbox states
        handle_checkbox_change()

        # Get the list of enabled channels
        enabled_channels = [channel["name"] for channel in channel_control if channel["status"] == "Enabled"]

        if len(enabled_channels) == 0:  # Check if no channels are enabled
            print("No channels are enabled. Waiting for channels to be enabled...")
        else:
            # print(f"Enabled channels: {enabled_channels}")  # Debug: Check enabled channels
            data, addr = server_socket.recvfrom(9000) # Adjust buffer size for maximum size for jumbo packets
            if data:
                # Forward to localhost on port 2000
                server_socket.sendto(data, ("127.0.0.1", 2000))
                packet_count += 1
                # print(f"Total packets received: {packet_count}")
                # Access the payload
                network_order_buffer = convert_buffer_to_network_order(data)
                # Calculate the number of samples per channel
                num_samples = len(network_order_buffer) // (2 * len(enabled_channels))
                # print(f"num_samples per channel: {num_samples}")
                # Initialize new_data with empty lists for each enabled channel
                new_data = [[] for _ in range(len(enabled_channels))]

                # Process data for enabled channels
                for i in range(num_samples):
                    for idx, channel_name in enumerate(enabled_channels):
                        # Extract 16 bits (2 bytes) for each enabled channel in cyclic order
                        start_idx = (i * len(enabled_channels) + idx) * 2
                        if start_idx + 1 < len(network_order_buffer):
                            value = (network_order_buffer[start_idx] << 8) | network_order_buffer[start_idx + 1]
                            new_data[idx].append(value)

                # Pad channels with no data to ensure uniform length
                max_length = max(len(channel) for channel in new_data)
                new_data = [channel + [0] * (max_length - len(channel)) for channel in new_data]

                # Convert new_data to signed 16-bit integers
                new_data = [list(map(lambda x: ((x + 2**15) % 2**16 - 2**15), channel)) for channel in new_data]
                # Convert new_data to numpy array for better handling
                new_data_matrix = np.array(new_data)
                update_subplots(new_data_matrix)
            else:
                print("No data received.")
    except BlockingIOError:
        # Suppress the error when no data is available
        pass
    except socket.error as e:
        print(f"Socket error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    # Always schedule the next call to handle_client
    root.after(100, handle_client, server_socket)

def run_server():
    server_address = ('192.168.0.10', 22136)  # Replace with your machine's IP address
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.bind(server_address)
        test_socket.close()
    except OSError:
        print(f"⚠️ WARNING: A UDP server is already running at {server_address[0]}:{server_address[1]}. Plotting functionality will be disabled.")
        print("However, you can still select channels and choose the modulation type.")
        return  # Do not create or schedule anything

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_address)
    server_socket.setblocking(False)
    print('Running UDP server on 192.168.0.10:22136...')
    root.after(100, handle_client, server_socket)

# Print the initial setup message
print("\n" + "*" * 40)
print("      -- Setting up adrv9009 chip --")
print("*" * 40 + "\n")

sdr  = adi.adrv9009_zu11eg(talise_uri)

sdr.tx_enabled_channels = [0, 1]
sdr.trx_lo = 2400000000
sdr.tx_hardwaregain_chan0 = 0
sdr.tx_hardwaregain_chan1 = 0
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"

# Read properties
print("TRX LO %s" % (sdr.trx_lo))

fs = int(sdr.tx_sample_rate)

print(fs)
fc = 5e6  # Carrier frequency for the I/Q signal
N = 6144
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.sin(2 * np.pi * fc * t)
q = - np.cos(2 * np.pi * fc * t)

modulation_options = [
    ("16QAM", "1"),
    ("64QAM", "2"),
    ("8PSK", "3"),
    ("BPSK", "5"),
    ("CPFSK", "6"),
    ("GFSK", "8"),
    ("PAM4", "9"),
    ("QPSK", "10"),
    ("ORIGINAL", "11")
]
selected_modulation = tk.StringVar(value="11")  # Default to ORIGINAL

mod_8spk  = scipy.io.loadmat('modulated_data/mod_8PSK.mat')
mod_16qam = scipy.io.loadmat('modulated_data/mod_16QAM.mat')
mod_64qam = scipy.io.loadmat('modulated_data/mod_64QAM.mat')
mod_bspk  = scipy.io.loadmat('modulated_data/mod_BPSK.mat')
mod_cpfsk = scipy.io.loadmat('modulated_data/mod_CPFSK.mat')
mod_gfsk  = scipy.io.loadmat('modulated_data/mod_GFSK.mat')
mod_pam4  = scipy.io.loadmat('modulated_data/mod_PAM4.mat')
mod_qpsk  = scipy.io.loadmat('modulated_data/mod_QPSK.mat')

def transmit_modulation():
    modulation_number = selected_modulation.get()
    modulation_type = next((text for text, value in modulation_options if value == modulation_number), "ORIGINAL")
    print(f"Selected modulation: {modulation_type}")

    match modulation_type:
        case "BPSK":
            data = mod_bspk['rx']
        case "QPSK":
            data = mod_qpsk['rx']
        case "8PSK":
            data = mod_8spk['rx']
        case "16QAM":
            data = mod_16qam['rx']
        case "64QAM":
            data = mod_64qam['rx']
        case "PAM4":
            data = mod_pam4['rx']
        case "GFSK":
            data = mod_gfsk['rx']
        case "CPFSK":
            data = mod_cpfsk['rx']
        case "ORIGINAL":
            data = i + 1j * q
            sdr.tx_destroy_buffer()
        case _:
            data = i + 1j * q
            sdr.tx_destroy_buffer()

    data = data.flatten()
    iq_real = np.int16(np.real(data) * 2**12-1)
    iq_imag = np.int16(np.imag(data) * 2**12-1)
    iq = iq_real + 1j * iq_imag

    sdr.tx_destroy_buffer()
    sdr.tx([iq, iq])

transmit_modulation()

# Add radio buttons for modulation selection
mod_label = tk.Label(control_frame, text="Select Modulation:")
mod_label.pack(anchor=tk.W, pady=(10, 0))

for text, value in modulation_options:
    tk.Radiobutton(
        control_frame, text=text, variable=selected_modulation, value=value
    ).pack(anchor=tk.W)

transmit_button = tk.Button(control_frame, text="Apply Selected Modulation", command=transmit_modulation)
transmit_button.pack(pady=10)

# Run the server
run_server()

# Add protocol handler to clean up on window close
def on_closing():
    sdr.tx_destroy_buffer()
    root.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter event loop
root.mainloop()