# ADSY1100 Testing

The ADSY1100 test suite is a collection of tests that are used to verify the functionality of the ADSY1100 device. The tests are written in Python and use the pytest framework.

## Instrument Configuration

Instrument configuration is done through the pybench_inst.yaml file. This file is used to configure the instrument settings for the test suite. The file is located in the test/adsy1100 directory.

## Run pytest

```bash
python -m pytest -vs test/adsy1100/test_smoke.py --configfile=test/adsy1100/pybench_inst.yaml  --html=testhtml/report.html --junitxml=testxml/report.xml --skip-scan
```