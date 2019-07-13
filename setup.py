import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyadi-iio",
    version="0.0.2",
    author="Travis Collins",
    author_email="travis.collins@analog.com",
    description="Interfaces to stream data from ADI hardware",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/analogdevicesinc/pyadi-iio",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
