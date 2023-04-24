import random
from decimal import Decimal
from test.common import (
    dev_interface,
    dev_interface_sub_channel,
    pytest_collection_modifyitems,
    pytest_configure,
)

import adi
import numpy as np
import pytest


def floor_step_size(quantity, step_size):
    """Quantize to specific stepsize

    parameters:
        quanity: type=float
            Value to be quantized
        step_size: type=str
            Step size to quantize quanity to
    """
    step_size_dec = Decimal(str(step_size))
    return float(int(Decimal(str(quantity)) / step_size_dec) * step_size_dec)


def attribute_single_value(
    uri, classname, attr, start, stop, step, tol, repeats=1, sub_channel=None
):
    """attribute_single_value:
    Write and read back integer class property
    This is performed a defined number of times and the value written
    is randomly determined based in input parameters

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        start: type=integer
            Lower bound of possible values attribute can be
        stop: type=integer
            Upper bound of possible values attribute can be
        step: type=integer
            Difference between successive values attribute can be
        tol: type=integer
            Allowable error of written value compared to read back value
        repeats: type=integer
            Number of random values to tests. Generated from uniform distribution
        sub_channel: type=string
            Name of sub channel (nested class) to be tested
    """
    # Pick random number in operational range
    numints = int((stop - start) / step)
    for _ in range(repeats):
        ind = random.randint(0, numints)
        val = start + step * ind
        if isinstance(val, float):
            val = floor_step_size(val, str(step))
        # Check hardware
        if sub_channel:
            assert dev_interface_sub_channel(
                uri, classname, sub_channel, val, attr, tol
            )
        else:
            assert dev_interface(uri, classname, val, attr, tol)


def attribute_single_value_boolean(uri, classname, attr, value):
    """attribute_single_value_boolean: Write and read back boolean class property

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        val: type=string
            Value to write and read back from attribute
    """
    bi = eval(classname + "(uri='" + uri + "')")
    setattr(bi, attr, value)
    rval = getattr(bi, attr)
    del bi
    assert rval == value


def attribute_single_value_str(uri, classname, attr, val, tol):
    """attribute_single_value_str: Write and read back string class property

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        val: type=string
            Value to write and read back from attribute
        tol: type=integer
            Allowable error of written value compared to read back value
    """
    # Check hardware
    assert dev_interface(uri, classname, str(val), attr, tol)


def attribute_single_value_readonly(
    uri, classname, attr, lower, upper, repeats=1, sub_channel=None
):
    """attribute_single_value:
    Write and read back integer class property
    This is performed a defined number of times and the value written
    is randomly determined based in input parameters

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        lower: type=integer or float
            Lower bound of possible values attribute can be
        upper: type=integer or float
            Upper bound of possible values attribute can be
        repeats: type=integer
            Number of random values to tests. Generated from uniform distribution
        sub_channel: type=string
            Name of sub channel (nested class) to be tested
    """

    for _ in range(repeats):

        val = (upper + lower) / 2  # center point
        tol = (upper - lower) / 2  # half the range
        # print("subchannel: ", sub_channel)
        # print("val: ", val)
        # print("tol: ", tol)

        # Check hardware
        if sub_channel:
            assert dev_interface_sub_channel(
                uri, classname, sub_channel, val, attr, tol, readonly=True
            )
        else:
            assert dev_interface(uri, classname, val, attr, tol, readonly=True)


def attribute_single_value_pow2(uri, classname, attr, max_pow, tol, repeats=1):
    """attribute_single_value_pow2: Write and read back integer class property
    where the integer is a power of 2. This is performed a defined
    number of times and the value written is randomly determined based
    in input parameters

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        max_pow: type=integer
            Largest power of 2 attribute allow to be
        tol: type=integer
            Allowable error of written value compared to read back value
        repeats: type=integer
            Number of random values to tests. Generated from uniform distribution
    """
    # Pick random number in operational range
    nums = [2 ** k for k in range(max_pow)]
    for _ in range(repeats):
        ind = random.randint(0, len(nums) - 1)
        val = nums[ind]
        # Check hardware
        assert dev_interface(uri, classname, val, attr, tol)


def attribute_multipe_values(uri, classname, attr, values, tol, repeats=1, sleep=0):
    """attribute_multipe_values: Write and read back multiple class properties
    in a loop where all values are pre-defined. This is performed a defined
    number of times.

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        values: type=list
            A list of values to write and check as attributes
        tol: type=integer
            Allowable error of written value compared to read back value
        repeats: type=integer
            Number of times to repeatedly write values
    """
    for _ in range(repeats):
        for val in values:
            if isinstance(val, str):
                assert dev_interface(uri, classname, val, attr, 0, sleep=sleep)
            else:
                assert dev_interface(uri, classname, val, attr, tol, sleep=sleep)


def attribute_multipe_values_with_depends(
    uri, classname, attr, depends, values, tol, repeats=1
):
    """attribute_multipe_values_with_depends: Write and read back multiple class
    properties in a loop where all values are pre-defined, where a set of
    dependent attributes are written first. This is performed a defined
    number of times.

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        depends: type=list
            A list of dependent values to write and check as attributes
        values: type=list
            A list of values to write and check as attributes
        tol: type=integer
            Allowable error of written value compared to read back value
        repeats: type=integer
            Number of times to repeatedly write values
    """
    # Set custom dependencies for the attr being tested
    for p in depends.keys():
        if isinstance(depends[p], str):
            assert dev_interface(uri, classname, depends[p], p, 0)
        else:
            assert dev_interface(uri, classname, depends[p], p, tol)
    for _ in range(repeats):
        for val in values:
            if isinstance(val, str):
                assert dev_interface(uri, classname, val, attr, 0)
            else:
                assert dev_interface(uri, classname, val, attr, tol)


def attribute_write_only_str(uri, classname, attr, value):
    """attribute_write_only_str: Write only string class property

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        value: type=string
            Value to write into attr property
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    try:
        setattr(sdr, attr, value)
        del sdr
    except Exception as e:
        del sdr
        raise Exception(e)


def attribute_write_only_str_with_depends(uri, classname, attr, value, depends):
    """attribute_write_only_str_with_depends: Write only string class
    property with dependent write only properties

    parameters:
        uri: type=string
            URI of IIO context of target board/system
        classname: type=string
            Name of pyadi interface class which contain attribute
        attr: type=string
            Attribute name to be written. Must be property of classname
        value: type=string
            Value to write into attr property
        depends: type=dict
            Dictionary of properties to write before value is written. Keys
            are properties and values are values to be written
    """
    sdr = eval(classname + "(uri='" + uri + "')")
    for p in depends:
        setattr(sdr, p, depends[p])
    try:
        setattr(sdr, attr, value)
        del sdr
    except Exception as e:
        del sdr
        raise Exception(e)
