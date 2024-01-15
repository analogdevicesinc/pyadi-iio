# CN0565
## 1. Install Prerequisite:

```cmd
pip install -r requirements.txt
pip install -e .
```
From the pyadi-iio main folder, install the prerequisites.
```cmd
pip install -r requirements.txt
```
After running this command, pip will read the requirements.txt file and install the specified packages along with their dependencies.

## 2. Run Example Script:
### Single Query
This will perform a single impedance measurement across a given electrode combinations.
```
python cn0565_example_single.py <f+> <f-> <s+> <s->

```
For example:
```cmd
python cn0565_example_single.py 0 3 1 2
```
This will use electrodes 0 and 3 for excitation and electrodes 1 and 2 for sensing.
### Running Multiple Measurements
This will perform  the impedance across different possible electrode combinations.
```cmd
python cn0565_example.py
```
### Running EIT Examples
These examples uses [PyEIT](https://github.com/eitcom/pyEIT)
#### Back Projection
```cmd
python cn0565_back_projection.py
```
#### Jacobian
```cmd
python cn0565_jacobian.py
```
#### GREIT
```cmd
python cn0565_greit.py
```
#### All EIT Plots
```cmd
python cn0565_sample_plot.py
```

## 3. To run the GUI:
```cmd
python main.py
```
This will start the GUI for the Electrical Impedance Tomography Measurement System.
