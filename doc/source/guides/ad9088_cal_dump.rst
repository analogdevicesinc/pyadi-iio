AD9084/AD9088 Calibration Data Dump Tool
==================================

The ``ad9088-cal-dump`` tool is a command-line utility for reading, validating, and analyzing AD9088 (and AD9084) calibration data files. It provides comprehensive information about calibration header structure, data sections, and CRC validation. Additionally, it supports remote calibration file transfer via SSH for seamless integration with networked test equipment.

Installation
------------

The tool is included with pyadi-iio and can be installed as a console script entry point:

.. code-block:: bash

    pip install pyadi-iio[jesd]

The ``[jesd]`` optional dependency includes ``paramiko``, which is required for SSH functionality.

Basic Usage
-----------

Local File Analysis
~~~~~~~~~~~~~~~~~~~

To analyze a calibration file on your local system:

.. code-block:: bash

    ad9088-cal-dump /path/to/calibration_file.bin

This will display:

- **Header Information**: Magic number, version, chip ID, and configuration
- **CRC Validation**: Calculated vs. stored CRC with status
- **Calibration Sections**: ADC, DAC, SERDES RX, and SERDES TX data summaries
- **Data Analysis**: Per-item breakdown and initialization status checks

Example output:

.. code-block:: text

    File: calibration_data.bin
    Size: 61908 bytes

    === CRC Validation ===

    Stored CRC:     0x001B3734
    Calculated CRC: 0x721B3734
    Status:         [FAILED]

    === AD9088 Calibration Data Header ===

    Magic Number:        0x41443930 ('09DA') [OK]
    Version:             1 [OK]
    Chip ID:             0x9088 (AD9088)
    Configuration:       4T4R (4 TX, 4 RX)
    Number of ADCs:      4
    Number of DACs:      4
    Number of SERDES RX: 2
    Number of SERDES TX: 2

    === Calibration Sections ===

    ADC Calibration:
      Offset: 0x00000040 (64 bytes)
      Size:   0x0000E500 (58624 bytes)
      Per Mode: 29312 bytes
      Per ADC:  7328 bytes

Remote Operations
-----------------

The tool supports SSH/SFTP operations for transferring calibration data to and from remote targets.

Downloading from a Remote Target
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``--ssh-pull`` command downloads a calibration file from a remote target via SSH. The tool supports flexible argument ordering with auto-discovery capabilities.

**Basic Syntax:**

.. code-block:: bash

    ad9088-cal-dump --ssh-pull <ip> <username> <password> [local_path] [remote_path]

**Parameters:**

- ``<ip>``: IP address or hostname of the remote target (required)
- ``<username>``: SSH username (required)
- ``<password>``: SSH password in plaintext (required)
- ``[local_path]``: (Optional) Local file path where calibration data will be saved. Defaults to ``calibration_data.bin`` if not specified.
- ``[remote_path]``: (Optional) Full path to calibration file on remote device. If omitted, the tool auto-discovers the file in ``/sys/bus/iio/devices/``.

**Usage Examples:**

Auto-discover calibration file on remote device:

.. code-block:: bash

    ad9088-cal-dump --ssh-pull 192.168.1.100 root mypassword

Download to default local filename (``calibration_data.bin``):

.. code-block:: bash

    ad9088-cal-dump --ssh-pull 192.168.1.100 root mypassword

Download and save to custom local filename:

.. code-block:: bash

    ad9088-cal-dump --ssh-pull 192.168.1.100 root mypassword my_backup.bin

Download from specific remote path to custom local filename:

.. code-block:: bash

    ad9088-cal-dump --ssh-pull 192.168.1.100 root mypassword my_backup.bin /lib/firmware/ad9088_cal.bin

**Auto-Discovery Behavior:**

When no ``remote_path`` is provided, the tool automatically searches for the calibration data file in:

.. code-block:: text

    /sys/bus/iio/devices/iio:device*/calibration_data

This is useful when the exact calibration file location is unknown or standard.

Uploading to a Remote Target
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``--ssh-push`` command uploads a calibration file to a remote target via SFTP.

**Syntax:**

.. code-block:: bash

    ad9088-cal-dump --ssh-push <ip> <username> <password> <local_path> <remote_path>

**Parameters:**

- ``<ip>``: IP address or hostname of the remote target (required)
- ``<username>``: SSH username (required)
- ``<password>``: SSH password in plaintext (required)
- ``<local_path>``: Full path to local calibration file to upload (required)
- ``<remote_path>``: Destination path on remote device where file will be saved (required)

**Example:**

.. code-block:: bash

    ad9088-cal-dump --ssh-push 192.168.1.100 root mypassword ./local_cal.bin /lib/firmware/ad9088_cal.bin

**Pre-Upload Validation:**

The tool automatically validates the local file before uploading:

- Verifies file exists and is readable
- Checks CRC32 checksum against stored value
- Validates magic number and version
- Validates file structure

If validation fails, the upload is aborted to prevent corrupting the target device.

File Format Details
-------------------

Calibration Header Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The calibration file begins with a 56-byte header containing:

- **Magic Number** (4 bytes): 0x41443930 (``"AD90"``)
- **Version** (4 bytes): File format version (currently 1)
- **Chip ID** (4 bytes): 0x9084 for AD9084, 0x9088 for AD9088
- **Configuration** (5 bytes): Chip configuration flags and device counts
  - ``is_8t8r``: 8T8R (1) or 4T4R (0)
  - ``num_adcs``: Number of ADC channels
  - ``num_dacs``: Number of DAC channels
  - ``num_serdes_rx``: Number of SERDES RX packs
  - ``num_serdes_tx``: Number of SERDES TX packs
- **Offsets** (16 bytes): Starting byte offset for each calibration section
- **Sizes** (16 bytes): Byte length for each calibration section
- **Total Size** (4 bytes): Total file size including CRC
- **Reserved** (3 bytes): Padding for alignment

Data Sections
~~~~~~~~~~~~~

The calibration data is organized into four main sections:

**ADC Calibration**
  Contains calibration data for analog-to-digital converters. Data is organized by calibration mode and ADC channel.

**DAC Calibration**
  Contains calibration data for digital-to-analog converters. Data is organized by DAC channel.

**SERDES RX Calibration**
  Contains receiver-side high-speed serializer/deserializer calibration data organized in 12-lane packs.

**SERDES TX Calibration**
  Contains transmitter-side high-speed serializer/deserializer calibration data organized in 12-lane packs.

CRC Validation
~~~~~~~~~~~~~~

The last 4 bytes of the file contain a CRC32 checksum (little-endian) that covers all preceding data. The tool automatically:

- Calculates CRC32 of all data except the last 4 bytes
- Compares with the stored value
- Reports validation status

All data is assumed to be in little-endian format (Intel byte order).

Troubleshooting
---------------

CRC Validation Failure
~~~~~~~~~~~~~~~~~~~~~~

**Issue**: The tool reports a CRC mismatch.

**Causes**:
- File is corrupted or incomplete
- File was transferred without binary mode (text mode corrupted it)
- File is from a different version or format

**Solution**: Verify the file integrity and re-download if necessary.

SSH Connection Failures
~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Cannot connect to the remote target.

**Causes**:
- Incorrect IP address or hostname
- Invalid username or password
- SSH port is blocked or not accessible
- Target device does not support SSH

**Solution**:
- Verify IP and credentials
- Test SSH connectivity manually: ``ssh username@ip``
- Check target device documentation for SSH availability

File Not Found (Remote)
~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Remote calibration file not found when using ``--ssh-pull``.

**Causes**:
- Incorrect remote path
- File doesn't exist on the target device
- Insufficient permissions to read the file

**Solution**:
- Verify the full path on the target device
- Check file permissions: ``ssh username@ip ls -la /path/to/file``
- Use the auto-discovery feature if supported by your device

Validation Failed Before Upload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Local file validation fails during ``--ssh-push``.

**Causes**:
- Corrupted local file
- Invalid magic number or version
- CRC mismatch in local file

**Solution**:
- Verify the local file with: ``ad9088-cal-dump /path/to/file``
- Ensure the file was obtained from a trusted source
- Re-download or regenerate the calibration file

Examples
--------

Complete Workflow
~~~~~~~~~~~~~~~~~

A typical workflow for backing up and analyzing calibration data:

.. code-block:: bash

    # 1. Download calibration from production device to custom filename
    ad9088-cal-dump --ssh-pull 192.168.1.100 root mypass prod_backup.bin /lib/firmware/ad9088_cal.bin

    # 2. Analyze the backup locally
    ad9088-cal-dump prod_backup.bin

    # 3. Make a timestamped backup copy
    cp prod_backup.bin "prod_cal_$(date +%Y%m%d_%H%M%S).bin"

    # 4. Later, restore to device
    ad9088-cal-dump --ssh-push 192.168.1.100 root mypass prod_backup.bin /lib/firmware/ad9088_cal.bin

Alternatively, use auto-discovery to download without specifying the remote path:

.. code-block:: bash

    # 1. Auto-discover and download calibration data
    ad9088-cal-dump --ssh-pull 192.168.1.100 root mypass prod_backup.bin

    # 2. Analyze the backup
    ad9088-cal-dump prod_backup.bin

Batch Operations
~~~~~~~~~~~~~~~~

For testing multiple devices, use shell scripting. Here are two examples:

**Batch Download with Custom Filenames:**

.. code-block:: bash

    #!/bin/bash

    DEVICES=("192.168.1.100" "192.168.1.101" "192.168.1.102")
    USERNAME="root"
    PASSWORD="mypass"
    REMOTE_PATH="/lib/firmware/ad9088_cal.bin"

    for device in "${DEVICES[@]}"; do
        local_file="cal_${device//./}.bin"
        echo "Processing $device -> $local_file..."
        ad9088-cal-dump --ssh-pull "$device" "$USERNAME" "$PASSWORD" "$local_file" "$REMOTE_PATH"
    done

**Batch Download with Auto-Discovery:**

.. code-block:: bash

    #!/bin/bash

    DEVICES=("192.168.1.100" "192.168.1.101" "192.168.1.102")
    USERNAME="root"
    PASSWORD="mypass"

    for device in "${DEVICES[@]}"; do
        local_file="cal_${device//./}.bin"
        echo "Processing $device -> $local_file..."
        # Auto-discover calibration file location
        ad9088-cal-dump --ssh-pull "$device" "$USERNAME" "$PASSWORD" "$local_file"
    done

See Also
--------

- `Analog Devices Documentation <https://www.analog.com/>`_
- `pyadi-iio GitHub Repository <https://github.com/analogdevicesinc/pyadi-iio>`_
- `AD9088 Device Documentation <https://www.analog.com/en/products/ad9088.html>`_
