from invoke import task
import os
import sys


def try_import():
    try:
        import iio

        return True
    except:
        return False


@task
def libiiopath(c):
    if not try_import():
        # Maybe its not on path
        if not os.name == "nt":
            # Try to add the correct directory to path
            for k in range(1, 8):
                temp = "/usr/lib/python3.{}/site-packages".format(v)
                if os.path.isdir(temp):
                    sys.path.append(temp)
                    if try_import():
                        not_installed = True
                    else:
                        print("---libiio found in directory %s---" % (temp))
                    break
        else:
            not_installed = True
        if not_installed:
            print("---libiio not found---")
    else:
        print("---libiio already on path---")


@task
def build(c, docs=False):
    c.run("python setup.py build")
    if docs:
        c.run("sphinx-build docs doc/_build")


@task
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
