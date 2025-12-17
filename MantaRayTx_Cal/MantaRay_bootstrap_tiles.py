import numpy as np
import time
import paramiko
import sys


# ######################################################
# Run the bootstrap script and block until it completes
########################################################

## Setup SSH conection into Talise SOM for control ##
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")

bootstrap_needed = True
if bootstrap_needed == True:
    boot_cmd = "bash manta_ray_adar1000_boot.bash"
    stdin, stdout, stderr = ssh.exec_command(boot_cmd,get_pty=True)
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