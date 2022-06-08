# type:ignore
# flake8: noqa
import os
import sys

from invoke import task


def try_import():
    try:
        import iio

        print("---IIO version found:", iio.version)
        return True
    except ImportError:
        return False


def add_libiio(do_prints=False, add_to_path=False):
    not_installed = False
    if not try_import():
        # Maybe its not on path
        if not os.name == "nt":
            # Try to add the correct directory to path
            for p in ["/usr/local", "/usr"]:
                for v in range(2, 4):
                    for k in range(1, 9):
                        temp = p + "/lib/python{}.{}/site-packages".format(v, k)
                        if os.path.isdir(temp):
                            sys.path.append(temp)
                            if not try_import():
                                not_installed = True
                            else:
                                if do_prints:
                                    print(
                                        "---libiio found in directory %s ---" % (temp)
                                    )
                                    print(
                                        "---Add to path with: export PYTHONPATH=$PYTHONPATH:%s"
                                        % (temp)
                                    )
                                # if add_to_path:
                                #     os.environ["PYTHONPATH"] = sys.path
                                return False
                            break
        else:
            if do_prints:
                print("Automatic module search only works on Linux right now")
            not_installed = True
            return False
        if not_installed:
            if do_prints:
                print("---libiio not found---")
            return False
    else:
        if do_prints:
            print("---libiio is already on path---")
        return True


@task
def libiiopath(c):
    """Search for libiio python bindings"""
    add_libiio(do_prints=True)


@task
def setup(c):
    """Install required python packages for development through pip"""
    c.run("pip3 install -r requirements.txt")
    c.run("pip3 install -r requirements_dev.txt")
    c.run("pip3 install -r requirements_doc.txt")
    print("---Python packages all setup (be sure to verify libiio is installed)")


@task
def builddoc(c):
    """Build sphinx doc"""
    c.run("sphinx-build doc/source doc/build")


@task(builddoc)
def build(c, docs=False):
    """Build python package"""
    c.run("python setup.py build")


@task(
    help={
        "message": "Custom message for tag. Defaults to `Beta release vXX`, where XX is auto determined",
        "inc": "Revision class increment position. major=X.2.3, minor==1.X.3, rev==1.2.X. Defaults to rev",
    }
)
def createrelease(c, message=None, inc="rev"):
    """Create GitHub release

    The following is performed:
    1. Test are run to check passing
    2. Tag is created
    3. __version__ file is updated with bumped version
    4. Commit is created for updated __version__ file

    Note that nothing is pushed!
    """
    # Check all tests are passing
    import pytest

    e = pytest.main(["-q"])
    if e:
        raise Exception("Some tests are failing, cannot create release")

    # Create tag from version
    import adi

    v = adi.__version__
    if not message:
        message = "Beta release v{}".format(v)
    cmd = 'git tag -a v{} -m "{}"'.format(v, message)
    print("Creating tagged commit")
    c.run(cmd)

    # Bump version and create commit
    import fileinput

    for line in fileinput.input("adi/__init__.py", inplace=True, backup=".bkp"):
        if line.find("__version__") > -1:
            l = line[len("__version__ = ") + 1 :].strip()[:-1].split(".")
            if inc == "major":
                major = int(l[0]) + 1
                minor = 0
                rev = 0
            elif inc == "minor":
                major = int(l[0])
                minor = int(l[1]) + 1
                rev = 0
            else:
                major = int(l[0])
                minor = int(l[1])
                rev = int(l[2]) + 1
            line = '__version__ = "{}.{}.{}"\n'.format(major, minor, rev)
            ver_string = "v{}.{}.{}".format(major, minor, rev)
        print(line, end="")
    c.run("git add adi/__init__.py")
    c.run('git commit -s -m "Bump to version {}"'.format(ver_string))


@task
def test(c):
    """Run pytest tests"""
    if not add_libiio(do_prints=True):
        print("---libiio not on path. Need to add first before testing")
    else:
        c.run("python3 -m pytest -v")


@task
def checkparts(c):
    """Check for missing parts in supported_parts.md"""
    print("Running supported_parts check")
    mod = __import__("adi")
    parts = []
    ignored_parts = [
        "ad9361",
        "ad9363",
        "ad9364",
        "adrv9009_zu11eg",
        "adrv9009_zu11eg_multi",
        "adrv9009_zu11eg_fmcomms8",
        "adar1000_array",
        "ad9081_mc",
        "ad717x",
    ]
    for c in dir(mod):
        if (
            any(c.lower().startswith(pre) for pre in ("ad", "hmc", "lt"))
            and not c in ignored_parts
        ):
            parts.append(c)
    # Check if in README
    count = 1
    with open("supported_parts.md") as reader:
        rm = reader.read()
        s = rm.find("### Currently supported hardware")
        e = rm.find("### Dependencies")
        rm = rm[s:e]
        count = 0
        for p in parts:
            p = p.replace("_", "-")
            if not p in rm.lower():
                count += 1
                print("Missing", p, "from README")
        if count == 0:
            print("No parts missing from supported_parts.md")

    print("------------------------")
    sys.exit(count)


@task(checkparts)
def precommit(c):
    """Run precommit checks"""
    c.run("pre-commit run --all-files")


@task
def changelog(c, since=None):
    """Print changelog from last release"""
    if not since:
        r = c.run(f"git describe --abbrev=0 --tags", encoding="utf-8", hide=True)
        since = r.stdout.splitlines()[0]
    r = c.run(f"git log {since}..HEAD --format=%s", encoding="utf-8", hide=True)
    changes = r.stdout.splitlines()
    print(f"Changes since {since}:")
    for change in changes:
        print(f"- {change}")


@task
def bumpversion_test(c):
    """Bump version to {current-version}.dev.{date}
    Used for marking development releases for test-pypi
    """
    import fileinput
    import time

    for line in fileinput.input("adi/__init__.py", inplace=True):
        if line.find("__version__") > -1:
            l = line[len("__version__ = ") + 1 :].strip()[:-1].split(".")
            major = int(l[0])
            minor = int(l[1])
            rev = int(l[2])
            seconds = int(time.time())
            line = '__version__ = "{}.{}.{}.dev.{}"\n'.format(
                major, minor, rev, seconds
            )
            ver_string = "v{}.{}.{}.dev.{}".format(major, minor, rev, seconds)
        print(line, end="")

    print(f"Version bumped to {ver_string}")
