import paramiko
import time
import re
import sys

# ====== CONFIG ======
HOST = "192.168.0.1"
PORT = 22
USERNAME = "root"
PASSWORD = "analog"
THRESHOLD = 70        # °C threshold for alert
POLL_INTERVAL = 2.0      # seconds between checks
CMD = "iio_attr -c adar1000_csb* . | grep 'temp0'"  # remote command
# =====================

def get_remote_temps(ssh):
    """Run remote command and return list of all temperature readings."""
    try:
        stdin, stdout, stderr = ssh.exec_command(CMD)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if error:
            print(f"SSH Error: {error}")
            return []

        # Find all "value '###'" numbers
        temps = [float(x) for x in re.findall(r"value\s+'([0-9]+(?:\.[0-9]+)?)'", output)]
        return temps
    except Exception as e:
        print(f"Error reading temperatures: {e}")
        return []
    
def adc_to_celsius(code):
    """Convert ADAR1000 temp ADC code to degrees Celsius."""
    OFFSET = 135.0
    SLOPE = 0.8  # LSB per °C
    return (code - OFFSET) / SLOPE


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {HOST}...")
        ssh.connect(hostname=HOST, port=PORT, username=USERNAME, password=PASSWORD)
        print(f"Connected. Monitoring all ADAR1000 temps (threshold = {THRESHOLD}°C)")

        while True:
            temps = get_remote_temps(ssh)
            temps = [adc_to_celsius(t) for t in temps]
            if temps:
                max_temp = max(temps)
                avg_temp = sum(temps) / len(temps)
                print(f"Temps: {temps}")
                print(f"→ Max: {max_temp:.1f} °C | Avg: {avg_temp:.1f} °C | Chips: {len(temps)}")

                if max_temp > THRESHOLD:
                    print("🔥 ALERT: A device exceeded threshold! 🔥")
                    sys.stdout.write('\a')  # terminal bell
                    sys.stdout.flush()
            else:
                print("Warning: Could not read temperatures.")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        ssh.close()
        print("SSH connection closed.")

if __name__ == "__main__":
    main()
