+ad7625
+=================
+
+By default, the device_name parameter in the class constructor is the
+same as the class name. To use the class with another supported model,
+the name must be given when instantiating the object. For example, if
+working with an ad7626 with a URI of "10.2.5.222", use the ad7625 class,
+but specify the device_name parameter explicitly:
+
+.. code-block:: bash
+
+   import adi
+   adc = adi.ad7625(uri="ip:10.2.5.222", device_name="ad7626")
+   ...
+
+
+.. automodule:: adi.ad7625
+   :members:
+   :undoc-members:
+   :show-inheritance:
