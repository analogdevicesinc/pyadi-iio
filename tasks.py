import inspect
import os
import sys

from invoke import task


def try_import():
    try:
        import iio

        return True
    except:
        return False


@task
def libiiopath(c):
    not_installed = False
    if not try_import():
        # Maybe its not on path
        if not os.name == "nt":
            # Try to add the correct directory to path
            for k in range(1, 8):
                temp = "/usr/lib/python2.{}/site-packages".format(k)
                if os.path.isdir(temp):
                    sys.path.append(temp)
                    if not try_import():
                        not_installed = True
                    else:
                        print("---libiio found in directory %s ---" % (temp))
                        print(
                            "---Add to path with export PYTHONPATH=$PYTHONPATH:%s"
                            % (temp)
                        )
                    break
        else:
            not_installed = True
        if not_installed:
            print("---libiio not found---")
    else:
        print("---libiio is already on path---")


@task
def builddoc(c, docs=False):
    c.run("sphinx-build doc/source doc/build")


@task(builddoc)
def build(c, docs=False):
    c.run("python setup.py build")


@task
def createrelease(c, message=None, next="rev"):
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
            if next == "major":
                major = int(l[0]) + 1
                minor = 0
                rev = 0
            elif next == "minor":
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
    c.run("pytest -v")


@task
def checkparts(c):
    print("Running README check")
    mod = __import__("adi")
    parts = []
    missing = []
    ignored_parts = ["ad9361", "ad9363", "ad9364", "adrv9009_zu11eg"]
    for c in dir(mod):
        if c[:2] == "ad" and not c in ignored_parts:
            parts.append(c)
    # Check if in README
    with open("README.md") as reader:
        rm = reader.read()
        s = rm.find("### Currently supported hardware")
        e = rm.find("### Dependencies")
        rm = rm[s:e]
        for p in parts:
            if not p in rm.lower():
                print("Missing", p, "from README")
    print("------------------------")


@task(checkparts)
def precommit(c):
    c.run("pre-commit run --all-files")


@task
def changelog(c, since=None):
    if not since:
        r = c.run(f"git describe --abbrev=0 --tags", encoding="utf-8", hide=True)
        since = r.stdout.splitlines()[0]
    r = c.run(f"git log {since}..HEAD --format=%s", encoding="utf-8", hide=True)
    changes = r.stdout.splitlines()
    print(f"Changes since {since}:")
    for change in changes:
        print(f"- {change}")
