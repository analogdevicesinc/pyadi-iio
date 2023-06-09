# Copyright (C) 2021 Xiphos Systems Corp.
# SKIP LICENSE INSERTION
# SPDX short identifier: ADIBSD

from contextlib import suppress

import paramiko


class sshfs:
    """Minimal sshfs replacement"""

    def __init__(self, address, username, password, sshargs=None):
        if address.startswith("ip:"):
            address = address[3:]
        self.address = address
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        if password is None:
            with suppress(paramiko.ssh_exception.AuthenticationException):
                self.ssh.connect(self.address, username=self.username, password=None)

            self.ssh.get_transport().auth_none(self.username)
        else:
            self.ssh.connect(
                self.address,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False,
            )

    def _run(self, cmd):
        (_, out, err) = self.ssh.exec_command(cmd)  # pylint: ignore=B601
        stdout = out.read().decode().strip()
        stderr = err.read().decode().strip()

        return stdout, stderr

    def isfile(self, path):
        stdout, _ = self._run(f"test -f {path}; echo $?")
        return stdout == "0"

    def listdir(self, path):
        stdout, _ = self._run(f"ls -1 {path}")
        return stdout.split()

    def gettext(self, path, *kargs, **kwargs):
        stdout, _ = self._run(f"cat {path}")
        return stdout
