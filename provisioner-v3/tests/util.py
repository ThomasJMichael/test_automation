#!/usr/bin/env python3
"""Tests for aslinuxtester.util.Util"""
import os
import subprocess
import unittest
import warnings
from aslinuxtester import util

def ignore_warnings(test_func):
    """Decorator to defuse the python warnings system"""
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_func(self, *args, **kwargs)
    return do_test

class UtilUnitTest(unittest.TestCase):
    """Holds tests for Util class"""

    @ignore_warnings
    def setUp(self):
        """unittest analog to __init__"""
        self.cfg = {
            'ip_address'    : '10.100.70.52',
            'dev_username'  : 'root',
            'dev_password'  : 'password',
            'port'      : 22
        }

        self.util = util.Util(repo_dir=os.environ['PWD'], loglevel=util.logging.ERROR)
        self.util.connect(self.cfg, quiet=True)

    @ignore_warnings
    def test_run_command(self):
        """Tests running a command remotely via Util.run_command"""
        self.assertEqual(self.util.run_command('true', quiet=True), 0)

    @ignore_warnings
    def test_copy_and_get_file(self):
        """Creates a dummy file, copies to remote host, then copies back"""
        subprocess.run(['rm', '-rf', 'this /tmp/this /tmp/this2'])
        subprocess.run(['/bin/sh', '-c', 'mkdir -p this/is/a/dumb/test'])
        subprocess.run(['/bin/sh', '-c', 'echo "success" > this/is/a/dumb/test/but_it_works'])
        self.util.run_command('rm -rf /tmp/this', quiet=True)
        self.util.copy_file('this', 'this', quiet=True)
        self.util.get_file('this', '/tmp/this2', quiet=True)
        self.assertEqual(subprocess.run([
            'diff',
            '/tmp/this2/is/a/dumb/test/but_it_works',
            'this/is/a/dumb/test/but_it_works'
        ]).returncode, 0)

    @ignore_warnings
    def test_reboot_and_reconnect(self):
        """Rebots the remote host, then attempts to reconnect"""
        try:
            self.util.run_command('sudo reboot', quiet=True)
            util.time.sleep(1)
            self.util.connect(self.cfg, quiet=True)
            self.assertEqual(self.util.run_command('true', quiet=True), 0)
        except util.paramiko.ssh_exception.SSHException:
            raise AssertionError("Could not reconnect to the target")

if __name__ == "__main__":
    unittest.main()
