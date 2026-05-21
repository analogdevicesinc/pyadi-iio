ad9084
=================

AD9084 is a tiled chip with 2 halves or sides. The control interfaces are unified but the DMA and DDS controls are split into multiple methods. This is similar to ADRV9002 and its split DMA modes. There are multiple **rx** and **tx** methods to control the DMA and DDS for each side of the chip. The **rx** (and **rx1**) and **tx** (and **tx1**) methods are used to control the DMA and DDS for the first side of the chip. The **rx2** and **tx2** methods are used to control the DMA and DDS for the second side of the chip.

.. automodule:: adi.ad9084
   :members:
   :undoc-members:
   :show-inheritance:
