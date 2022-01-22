import re

import setuptools


# From: https://github.com/smartcar/python-sdk/blob/master/setup.py
def _get_version():
    """Extract version from package."""
    with open("adi/__init__.py") as reader:
        match = re.search(
            r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', reader.read(), re.MULTILINE
        )
        if match:
            return match.group(1)
        else:
            raise RuntimeError("Unable to extract version.")


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyadi-iio",
    version=_get_version(),
    author="Travis Collins",
    author_email="travis.collins@analog.com",
    description="Interfaces to stream data from ADI hardware",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/analogdevicesinc/pyadi-iio",
    packages=setuptools.find_packages(exclude=["test*"]),
    python_requires=">=3.6",
    install_requires=["numpy", "pylibiio==0.23.1"],
    extras_require={"jesd": ["paramiko"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
