MCP Server
===================

pyadi-iio includes a `Model Context Protocol <https://modelcontextprotocol.io/>`_ (MCP) server that enables AI assistants and other MCP clients to interact with ADI hardware at runtime. The server exposes tools for device discovery, connection management, property configuration, data capture, and signal generation across all supported device classes.

Installation
---------------------------

Install pyadi-iio with the MCP optional dependencies:

.. code-block:: bash

 pip install pyadi-iio[mcp]

This installs `fastmcp <https://github.com/jlowin/fastmcp>`_ and numpy as additional dependencies.

Running the Server
---------------------------

Start the MCP server using the installed entry point:

.. code-block:: bash

 pyadi-iio-mcp

Or run it directly as a module:

.. code-block:: bash

 python -m adi.mcp_server

The server communicates over stdio using the MCP protocol. To use it with an MCP client, configure the client to launch the server as a subprocess. For example, in a Claude Desktop ``claude_desktop_config.json``:

.. code-block:: json

 {
   "mcpServers": {
     "pyadi-iio": {
       "command": "pyadi-iio-mcp"
     }
   }
 }

Available Tools
---------------------------

The server provides the following tools:

Device Discovery
^^^^^^^^^^^^^^^^^

**list_device_classes** -- List all available pyadi-iio device classes with an optional name filter. This is useful for finding the correct class name for a specific part.

.. code-block:: python

 # Example tool call
 list_device_classes(filter_text="936")
 # Returns: ["ad9361", "ad9363", "ad9364"]

Connection Management
^^^^^^^^^^^^^^^^^^^^^^

**connect_device** -- Create a connection to any pyadi-iio device by class name and URI. Returns a ``connection_id`` UUID used by all subsequent tools, along with a summary of device capabilities.

.. code-block:: python

 # Connect to an AD9361-based device
 connect_device(device_class="ad9361", uri="ip:192.168.2.1")

 # Connect with extra constructor arguments
 connect_device(
     device_class="ad9084",
     uri="ip:192.168.2.1",
     kwargs='{"rx1_device_name": "axi-ad9084-rx-hpc"}',
 )

**disconnect_device** -- Close a connection and clean up resources.

Device Introspection
^^^^^^^^^^^^^^^^^^^^^

**discover_device_capabilities** -- Inspect a connected device to learn what it supports. Returns whether the device has RX, TX, and DDS capabilities, along with a list of all available properties including read/write metadata and documentation. An optional filter narrows the property list.

.. code-block:: python

 # See all properties related to "nco"
 discover_device_capabilities(connection_id="...", filter_text="nco")

Property Access
^^^^^^^^^^^^^^^^

**get_property** -- Read any device property by name. Works with any property exposed by the device class, from sample rates to NCO frequencies to gain settings.

.. code-block:: python

 get_property(connection_id="...", property_name="rx_sample_rate")

**set_property** -- Write any writable device property. The value is passed as a JSON-encoded string to support all types (integers, floats, lists, strings).

.. code-block:: python

 # Set a scalar value
 set_property(connection_id="...", property_name="rx_lo", value="2400000000")

 # Set a list value
 set_property(
     connection_id="...",
     property_name="rx_channel_nco_frequencies",
     value="[100000000, 200000000]",
 )

Data Capture
^^^^^^^^^^^^^

**capture_rx_data** -- Capture receive data and save it to a ``.npy`` file for analysis. Supports configurable buffer sizes and channel selection.

.. code-block:: python

 capture_rx_data(
     connection_id="...",
     output_path="/tmp/capture.npy",
     buffer_size=65536,
     enabled_channels="[0, 1]",
 )

Signal Generation
^^^^^^^^^^^^^^^^^^

**configure_dds** -- Configure the FPGA-side DDS to generate a single tone on a specified TX channel. Useful for loopback testing and spectral analysis.

.. code-block:: python

 configure_dds(
     connection_id="...", frequency=10000000, scale=0.9, channel=0,
 )


Example Workflow
---------------------------

A typical interaction with the MCP server follows this pattern:

1. **Discover** available device classes with ``list_device_classes``
2. **Connect** to hardware with ``connect_device``
3. **Explore** the device with ``discover_device_capabilities``
4. **Configure** the device with ``set_property``
5. **Capture** data with ``capture_rx_data`` or generate signals with ``configure_dds``
6. **Read back** configuration with ``get_property``
7. **Disconnect** when done with ``disconnect_device``

.. code-block:: python

 # 1. Find the right device class
 list_device_classes(filter_text="pluto")
 # -> ["Pluto"]

 # 2. Connect
 result = connect_device(device_class="Pluto", uri="ip:192.168.2.1")
 conn_id = result["connection_id"]

 # 3. Explore what the device can do
 discover_device_capabilities(connection_id=conn_id, filter_text="lo")

 # 4. Configure
 set_property(connection_id=conn_id, property_name="rx_lo", value="2400000000")
 set_property(connection_id=conn_id, property_name="sample_rate", value="2084000")

 # 5. Capture data
 capture_rx_data(connection_id=conn_id, output_path="/tmp/data.npy")

 # 6. Disconnect
 disconnect_device(connection_id=conn_id)

API Reference
---------------------------

.. automodule:: adi.mcp_server
   :members:
   :exclude-members: ConnectionManager, main
