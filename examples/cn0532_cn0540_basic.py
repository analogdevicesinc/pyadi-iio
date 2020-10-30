# Import the pyadi module
import adi

# Define the URI we use to connect to the remote device
uri = "ip:analog"
# Connect to the device
xl = adi.cn0532(uri)
# Set number of samples to capture
xl.rx_buffer_size = 2 ** 12
# Pull rx_buffer_size samples back from the device
data = xl.rx()
# Print data shape
print(data.shape)
