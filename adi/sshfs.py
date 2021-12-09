# Copyright (C) 2021 Xiphos Systems Corp.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from contextlib import suppress

import paramiko


class sshfs:

    """Minimal sshfs replacement"""

    def __init__(self, address: str, username: str, password: str):
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
        (_, out, err) = self.ssh.exec_command(cmd)
        stdout = out.read().decode().strip()
        stderr = err.read().decode().strip()

        return stdout, stderr

    def isfile(self, path: str):
        """Verify remote path exists

        Args:
            path (str): Path to check exists

        Return:
            bool: True is path exists, False otherwise
        """
        stdout, _ = self._run(f"test -f {path}; echo $?")
        return stdout == "0"

    def listdir(self, path: str):
        """List contexts of remote path. This will run 'ls -l' on provided path

        Args:
            path (str): Path to remote to run ls -l command on

        Return:
            str: Output of ls -l command
        """
        stdout, _ = self._run(f"ls -1 {path}")
        return stdout.split()

    def gettext(self, path: str):
        """Get text of specific path. This will run cat on provided path

        Args:
            path (str): Path to remote to run cat command on

        Return:
            str: Output of cat command
        """
        stdout, _ = self._run(f"cat {path}")
        return stdout
