import argparse

import pytest

try:
    from adi.tools.adistream import run_adi_stream
except:
    pytest.skip(allow_module_level=True)

hardware = "ad5780"
ref_neg = "-10"
ref_pos = "+10"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [("ad579x")])
@pytest.mark.parametrize("code_sel", ["0", "1"])
@pytest.mark.parametrize(
    "wave_types", ["sine", "cosine", "triangular", "square", "pwm"]
)
@pytest.mark.parametrize("v_lower_req, v_upper_req", [("-5", "5"), ("0", "10")])
@pytest.mark.parametrize("channel_order", ["asc", "desc"])
@pytest.mark.parametrize("output_freq", ["100", "500"])
def test_adistream_vaild_inputs(
    capsys,
    classname,
    iio_uri,
    code_sel,
    wave_types,
    v_lower_req,
    v_upper_req,
    channel_order,
    output_freq,
):
    run_adi_stream(
        [
            classname,
            iio_uri,
            ref_neg,
            ref_pos,
            "--output_freq",
            output_freq,
            "--code_sel",
            code_sel,
            "--wave_types",
            wave_types,
            "--v_lower_req",
            v_lower_req,
            "--v_upper_req",
            v_upper_req,
            "--channel_order",
            channel_order,
        ],
        True,
    )
    captured = capsys.readouterr()
    assert (
        captured.out == "Press escape key to stop cyclic data streaming..\n"
        "Data streaming started\n\r\n"
        "Data streaming finished\n"
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("wave_types", ["pwm"])
@pytest.mark.parametrize("duty_cycle", ["10", "50", "75", "90"])
@pytest.mark.parametrize("classname", [("ad579x")])
def test_adistream_dutycycle(capsys, classname, iio_uri, wave_types, duty_cycle):
    run_adi_stream(
        [
            classname,
            iio_uri,
            ref_neg,
            ref_pos,
            "--wave_types",
            wave_types,
            "--duty_cycle",
            duty_cycle,
        ],
        True,
    )
    captured = capsys.readouterr()
    assert (
        captured.out == "Press escape key to stop cyclic data streaming..\n"
        "Data streaming started\n\r\n"
        "Data streaming finished\n"
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("upper_req", ["15"])
@pytest.mark.parametrize("classname", [("ad579x")])
def test_adistream_voltages_1(classname, iio_uri, upper_req):
    with pytest.raises(Exception) as context:
        run_adi_stream(
            [classname, iio_uri, ref_neg, ref_pos, "--v_upper_req", upper_req], True
        )

    assert (
        str(context.value)
        == "required upper voltage cannot be greater than upper voltage reference"
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("lower_req", ["-15"])
@pytest.mark.parametrize("classname", [("ad579x")])
def test_adistream_voltages_2(classname, iio_uri, lower_req):
    with pytest.raises(Exception) as context:
        run_adi_stream(
            [classname, iio_uri, ref_neg, ref_pos, "--v_lower_req", lower_req], True
        )

    assert (
        str(context.value)
        == "required lower voltage cannot be less than lower voltage reference"
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("data_points", [("-10"), ("0")])
@pytest.mark.parametrize("classname", [("ad579x")])
def test_adistream_datapoints(classname, iio_uri, data_points):
    with pytest.raises(argparse.ArgumentTypeError) as context:
        run_adi_stream(
            [
                classname,
                iio_uri,
                ref_neg,
                ref_pos,
                "--data_points_per_wave",
                data_points,
            ],
            True,
        )

    assert str(context.value) == "data points must be greater than 0"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [("ad1234"), ("ad1123x")])
def test_adistream_invalid_classnames_1(classname, iio_uri):
    with pytest.raises(Exception) as context:
        run_adi_stream([classname, iio_uri, ref_neg, ref_pos], True)

    assert (
        str(context.value)
        == f"The device {classname} is not supported. Supported devices are: "
        "ad579x,ad3552r,ad3530r,ad5754r,ad9152,ad9172\n"
        "Enable test_device (-t) flag to test devices not part of the supported "
        "devices list."
    )


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("classname", [("ad1234"), ("ad1123x")])
def test_adistream_invalid_classnames_2(classname, iio_uri):
    with pytest.raises(AttributeError) as context:
        run_adi_stream([classname, iio_uri, ref_neg, ref_pos, "--test_device"], True)

    assert str(context.value) == f"module 'adi' has no attribute '{classname}'"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("output_freq", [("-10"), ("0")])
@pytest.mark.parametrize("classname", [("ad579x")])
def test_adistream_output_freq(classname, iio_uri, output_freq):
    with pytest.raises(argparse.ArgumentTypeError) as context:
        run_adi_stream(
            [classname, iio_uri, ref_neg, ref_pos, "--output_freq", output_freq], True
        )

    assert str(context.value) == "output frequency required cannot be a negative number"


#########################################
@pytest.mark.iio_hardware(hardware, True)
@pytest.mark.parametrize("duty_cycle", [("-10"), ("110")])
@pytest.mark.parametrize("classname", [("ad579x")])
def test_adistream_invalid_duty_cycle(classname, iio_uri, duty_cycle):
    with pytest.raises(argparse.ArgumentTypeError) as context:
        run_adi_stream(
            [classname, iio_uri, ref_neg, ref_pos, "--duty_cycle", duty_cycle], True
        )

    assert str(context.value) == "Duty cycle shall be in between 0 and 100"
