import numpy as np
import matplotlib as plt

poly_atten1 = [-4.178368227245296e-09, -3.124456767699238e-07, -7.218061870232358e-06,
                     1.146280656652001e-05, 0.003079353177989, 0.048281159204065,
                     0.247215102895886, 0.176811045216789, 10.163992861226674, 127.1237461140638]



import numpy as np
import matplotlib.pyplot as plt

# Define the coefficients of your polynomial (from highest to lowest degree)
# For example, coefficients = [2, -3, 5] represents the polynomial 2x² - 3x + 5
coefficients = poly_atten1 # You can change these to define your desired polynomial

# Define the range for the x-values
x_min = -24
x_max = 0
num_points = 20 # Number of points to generate for a smooth curve

# Generate a sequence of evenly spaced x-values within the specified range
x_values = np.linspace(x_min, x_max, num_points)

# Evaluate the polynomial at each x-value using numpy.polyval()
y_values = np.polyval(coefficients, x_values)

# Create the plot
plt.figure(figsize=(8, 6)) # Adjust figure size as needed
plt.plot(y_values, x_values, label=f"Polynomial: {coefficients[7]}x^2 + {coefficients[8]}x + {coefficients[9]}")  # customize the label based on your polynomial
plt.title("Polynomial Plot")  # Set plot title
plt.xlabel("X-axis")  # Label X-axis
plt.ylabel("Y-axis")  # Label Y-axis
plt.yticks(x_values)
plt.xticks(y_values)
plt.grid(True)  # Add a grid for better readability
plt.legend()  # Display the label defined in plt.plot()
plt.axhline(0, color='black', linewidth=0.5) # Add x-axis
plt.axvline(0, color='black', linewidth=0.5) # Add y-axis
plt.show() # Display the plot
