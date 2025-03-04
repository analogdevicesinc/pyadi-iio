import datetime
import random
import time

# Get the current system timestamp


# Write the timestamp to a file
while True:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("cnn_output.txt", "w") as file:
        file.write(timestamp + "\n")
        file.write(str(random.choice([1, 2, 3, 5, 6, 8,9,10])) + "\n")
        file.write(str(random.choice([1, 2, 3, 5, 6, 8,9,10])) + "\n")
        file.write(str(random.choice([1, 2, 3, 5, 6, 8,9,10])) + "\n")
        file.write(str(random.choice([1, 2, 3, 5, 6, 8,9,10])) + "\n")


        file.write(str(random.uniform(0, 1)) + "\n")
        file.write(str(random.uniform(0, 1)) + "\n")
        file.write(str(random.uniform(0, 1)) + "\n")
        file.write(str(random.uniform(0, 1)) + "\n")

    time.sleep(2)
