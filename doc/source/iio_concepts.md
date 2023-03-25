# Receiving and Sending Data

Remote data streaming to and from hardware is made available through unique interface class implementations, which are unique for each component or platform. These classes are used to both configure a given platform and move data back and forth from the device.

Command and control of hardware from Python is accomplished by leveraging the [IIO drivers](https://wiki.analog.com/software/linux/docs/iio/iio) built into the target platform's kernel and [libiio](https://wiki.analog.com/resources/tools-software/linux-software/libiio) which provides remote backends to control drivers across different backends. Backends can be Ethernet, serial, or USB based. Below is a diagram of the different components in the stack for an FMComms based systems, but will be similar for all systems.

![Python libiio Stack](assets/MATLAB_libiio_Stack.png)

Since libiio is cross-platform it can be used from Windows, Linux, or macOS based systems. It is also a lower level library independent of MATLAB, so when moving toward production or untethered systems similar APIs that are used in Python can be used in C,C++,MATLAB, or other languages.

## Connecting and Configuration

Connecting to hardware is done by setting the **uri** property of the system object interface. The **uri** for libiio always has the convention "*< backend >:< address >*", where *backend* can be ip,usb, or serial. *address* will be specific to the backend. This is documented in the [libiio API](https://analogdevicesinc.github.io/libiio/master/libiio/group__Context.html#gafdcee40508700fa395370b6c636e16fe).

Below is a basic example of setting up an AD9361 receiver using an Ethernet/IP backend where the address of the target system is 192.168.2.1:

```python
dev = adi.ad9680(uri="ip:192.168.2.1")
data = dev.rx()
```
With the code above, no actual configuration is performed on the device. The context is simply created by connecting to the hardware and enumerating the available configurations. Line 2 will configure local buffers to allow capturing of data first on the remote system and then on transfer it across the backend to a local host.

To provide a complete example we can do more advanced configuration like so to demonstrate property changes:
```linenums="1"
rx = adi.AD9361.Rx;
rx.uri = 'ip:192.168.2.1';
rx.SamplesPerFrame = 1024;
rx.CenterFrequency = 1e9;
dataLO1 = rx();

% Update tunable property
rx.CenterFrequency = 2e9;
dataLO2 = rx();

% Update non-tunable property
rx.release();
rx.SamplesPerFrame = 4096;
dataLargerBuffer = rx();
```

