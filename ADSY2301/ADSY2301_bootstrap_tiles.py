# ==========================================================================
# ADSY2301 — ADAR1000 Tile Bootstrap
# --------------------------------------------------------------------------
# Connects to the ADSY2301 SoM via SSH and runs the ADAR1000 bootstrap
# script on the target.  This must be executed once after every power cycle
# before any other ADSY2301 script.
#
# The bootstrap script takes approximately 4-5 minutes to complete.
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import time
import paramiko
import sys


# ==========================================================================
# Configuration
# ==========================================================================
HOSTNAME = "192.168.1.1"
USERNAME = "root"
PASSWORD = "analog"
BOOTSTRAP_NEEDED = True   # Set to False to skip bootstrap (e.g. tiles already initialised)

# ==========================================================================
# Run Bootstrap
# ==========================================================================
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=HOSTNAME, port=22, username=USERNAME, password=PASSWORD)

if BOOTSTRAP_NEEDED:
    print("Running ADAR1000 bootstrap — this takes ~4-5 minutes...")
    boot_cmd = "bash manta_ray_adar1000_boot.bash"
    stdin, stdout, stderr = ssh.exec_command(boot_cmd, get_pty=True)
    chan = stdout.channel

    # stream output while the command runs
    while not chan.exit_status_ready():
        if chan.recv_ready():
            out_chunk = chan.recv(1024).decode(errors="ignore")
            print(out_chunk, end="")
        if chan.recv_stderr_ready():
            err_chunk = chan.recv_stderr(1024).decode(errors="ignore")
            print(err_chunk, end="", file=sys.stderr)
        time.sleep(0.1)

    # flush any remaining output
    if chan.recv_ready():
        print(chan.recv(1024).decode(errors="ignore"), end="")
    if chan.recv_stderr_ready():
        print(chan.recv_stderr(1024).decode(errors="ignore"), end="", file=sys.stderr)

    exit_status = chan.recv_exit_status()
    if exit_status != 0:
        ssh.close()
        raise RuntimeError(f"Boot script failed (exit {exit_status})")
    else:
        print(f"Boot script completed (exit {exit_status})")
    ssh.close()