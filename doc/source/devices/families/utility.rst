Utility / Infrastructure
========================

Helper classes that don't represent a standalone end-user product:
JESD204 debug, generic mux drivers, TDD (time-division-duplex)
controllers, AXI trigger blocks, switches, and generic 1-bit
ADC/DAC for GPIO-style use.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 65 5

   * - Class
     - Highlights
     -
   * - :doc:`adi.jesd <../adi.jesd>`
     - JESD204 link debug. Requires the ``[jesd]`` extra (paramiko).
     -
   * - :doc:`adi.gen_mux <../adi.gen_mux>`
     - Generic mux / multiplexer driver
     -
   * - :doc:`adi.tdd <../adi.tdd>` / :doc:`adi.tddn <../adi.tddn>`
     - Time-division-duplex controllers (tdd: legacy, tddn: new)
     -
   * - :doc:`adi.axi_aion_trig <../adi.axi_aion_trig>`
     - AXI ION trigger control block (HDL trigger logic)
     -
   * - :doc:`adi.adg2128 <../adi.adg2128>`
     - 12×8 analog crosspoint switch matrix
     -
   * - :doc:`adi.one_bit_adc_dac <../adi.one_bit_adc_dac>`
     - GPIO exposed as 1-bit ADC / DAC for state control
     -

Mental model
------------

These classes don't share a common shape with the rest of the
library — they exist to give Python-level access to infrastructure
pieces (clocking debug, GPIO, switching) that appear alongside the
"main" data converters. Each has its own minimal API specific to its
purpose.

The ``adi.jesd`` class is the most commonly used: when a JESD ADC or
DAC isn't producing samples, it's the first place to look. It connects
over SSH to the FPGA-side debugfs and reports link state per lane.

Minimal example
---------------

.. code-block:: python

   import adi

   jesd = adi.jesd(address="192.168.2.1")
   print(jesd.get_status("ad9680_rx"))

Common properties
-----------------

Class-specific — see each class's autodoc.

Common gotchas
--------------

* ``adi.jesd`` requires paramiko (``pip install pyadi-iio[jesd]``) and
  SSH access to the FPGA-side OS. Won't work against a stripped-down
  embedded image without an SSH server.
* ``adi.tdd`` is the legacy interface; new HDL designs use the
  ``adi.tddn`` version. Picking the wrong one will report bogus values.
* ``adi.one_bit_adc_dac`` provides GPIO control through the IIO
  framework — useful for FPGA-controlled enables and resets, but the
  GPIO line has to be exposed in the device tree.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`Troubleshooting: JESD extras <../../guides/troubleshooting>`

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.adg2128
   ../adi.axi_aion_trig
   ../adi.gen_mux
   ../adi.jesd
   ../adi.one_bit_adc_dac
   ../adi.tdd
   ../adi.tddn
