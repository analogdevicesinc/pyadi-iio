import adi
import pytest

hardware = ["ad9371", "ad9144"]
classname = "adi.sshfs.sshfs"


def open_sshfs(classname, iio_uri, username, password):
    _password = f'"{password}"' if password is not None else None
    return eval(f'{classname}("{iio_uri}", "{username}", {_password})')


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
def test_sshfs_isfile(iio_uri, classname, username, password):
    sshfs = open_sshfs(classname, iio_uri, username, password)
    assert sshfs.isfile("/etc/os-release")
    assert sshfs.isfile("/etc/") == False


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.iio_hardware(hardware)
def test_sshfs_listdir(iio_uri, classname, username, password):
    sshfs = open_sshfs(classname, iio_uri, username, password)
    assert isinstance(sshfs.listdir("/etc/"), list)


@pytest.mark.iio_hardware(hardware)
@pytest.mark.parametrize("classname", [(classname)])
@pytest.mark.iio_hardware(hardware)
def test_sshfs_gettext(iio_uri, classname, username, password):
    sshfs = open_sshfs(classname, iio_uri, username, password)
    assert sshfs.gettext("/proc/version").startswith("Linux version")
