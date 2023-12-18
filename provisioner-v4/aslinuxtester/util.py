#!/usr/bin/env python3
"""Utilities for aslinuxtester module"""
from enum import IntEnum
from xml.dom import minidom
from shutil import copyfile
import random
import socket
import stat
import sys
import os
import json
import time
import logging
import inspect
import argparse
import subprocess
import requests
import winrm
import paramiko

logging.basicConfig(level=logging.INFO, format='%(levelname)s:[%(name)s]:%(message)s')

"""
def get_parent_key(d, value):
    for k,v in d.items():
        if isinstance(v, dict):
            p = get_parent_key(v, value)
            if p:
                return [k] + p
        elif v == value:
            return [k]
"""
class Util():
    """
    Shared functions, paths, and parameters for use throughout the provisioner system.

    Include by doing
    ```python
    from aslinuxtester.util import Util
    util = Util('/path/to/config/repo')
    ...
    ```

    There are several filepaths which can be set explicitly by manipulating the
    Util.local_filepaths and Util.remote_filepaths dictionaries.

    ```python
    # valid manually settable and their defaults are as follows
    self.local_filepaths['sshconfig']           # <repodir>/config/ssh
    self.local_filepaths['prereqscripts']       # <repodir>/scripts/prereqs
    self.local_filepaths['postreqscripts']      # <repodir>/scripts/postreqs
    self.local_filepaths['driverscripts']       # <repodir>/scripts/driver_installers
    self.local_filepaths['logs']                # ./logs

    self.remote_filepaths['prereqscripts']      # ./.scripts/abacoprecfg
    self.remote_filepaths['postreqscripts']     # ./.scripts/abacpostcfg
    self.remote_filepaths['driverscripts']      # ./drivers
    self.remote_filepaths['tests']              # ./tests
    ```
    """

    _client = None
    _output_file = None
    iboot = None
    logging = logging

    def __init__(self, **kwargs):
        """
        Calls Util.set_path with the supplied repo_dir. Prints a warning if repo_dir
        is left empty.

        Keyword args:
          - repo_dir (str): [.] Path to the configuration repository
          - outfile (str): [None] Path to an output file that all prints will go to
          - logger (str): ['alt'] Name of a python logger to use
          - loglevel (logging.LEVEL): [logging.INFO] Loglevel to print at
        """
        opts = {
            'repo_dir'  : '.',
            'outfile'   : None,
            'logger'    : 'alt',
            'loglevel'  : logging.INFO,
            'quiet'     : False
        }
        opts.update(kwargs)
        self.logger = logging.getLogger(opts['logger'])
        self.logger.setLevel(opts['loglevel'])
        logging.getLogger('paramiko').setLevel(logging.ERROR)

        if opts['repo_dir'] == '.':
            print(f"WARNING: repo_dir has defaulted to {os.path.abspath(opts['repo_dir'])}. "
                  f"Things may not work as expected.")
        if opts['outfile']:
            print(f'Opening {opts["outfile"]} for writing')
            self._output_file = logging.FileHandler(opts['outfile'])
            self._output_file.setLevel(logging.DEBUG)
            self.logger.addHandler(self._output_file)

        self.set_paths(opts['repo_dir'])
        self.print('Initialized utilities', logger='alt', quiet=opts['quiet'])
        #self.validator = Validator(util=self)

    def get_logger(self):
        """Returns the python logger in use by Util"""
        return self.logger

    ## FUNCTIONS ##
    def print(self, printstr, **kwargs):
        """
        Print helper that understands the 'quiet' option. Also prints to a file
        if one was configured at Util init.

        Args:
          - printstr (str): The string to print
        Keyword args:
          - quiet (bool): [False] Don't print to stdout, still prints to outfile
          - outfile (file): [None] File to log shenanigans in
          - end (str): ['\\n'] 'end' kwarg to pass to print function
          - use_logger (bool): [True] Use the logger instead of standard print
          - logger (str): [{modulename}.{fnname}] Logger child to use
          - level (logging.LEVEL): [logging.INFO] Log level to use
        """
        stack = inspect.stack()[1]
        opts = {
            'quiet'     : False,
            'file'      : None,
            'end'       : '\n',
            'use_logger': True,
            'logger'    : f'{inspect.getmodulename(stack[1])}.{stack[3]}',
            'level'     : logging.INFO
        }
        opts.update(kwargs)
        print(printstr, end=opts['end'])
        sys.stdout.flush()

    def set_paths(self, repo_dir):
        """
        Sets local and remote filepaths using the supplied repository path.

        Args:
          - repo_dir (str): Path to the configuration repository
        """
        self.local_filepaths = {
            'repo_dir'          : repo_dir,
            'pconfig'           : None,
            'sshconfig'         : f"{repo_dir}/config/ssh",
            'prereqscripts'     : f"{repo_dir}/scripts/prereqs",
            'postreqscripts'    : f"{repo_dir}/scripts/postreqs",
            'driverscripts'     : f"{repo_dir}/scripts/driver_installers",
            'posttestscripts'   : f"{repo_dir}/scripts/post_test",
            'logs'              : f'{repo_dir}/logs',
            'host_logs'         : f'{repo_dir}/tests/logs',
            'tests'             : f"{repo_dir}/tests",
            'complete_flag'     : '/tmp/config.json'
        }
        self.remote_filepaths = {
            'prereqscripts'     : '.scripts/abacoprecfg',
            'postreqscripts'    : '.scripts/abacopostcfg',
            'driverscripts'     : 'drivers',
            'sshconfig'         : '.ssh',
            'complete_flag'     : '.installed_config.json',
            'tests'             : 'tests'
        }

    def build_config(self, tgt_os, **kwargs):
        """
        Builds a configuration from a given provisioner config file and a target OS.

        Args:
          - tgt_os (str): The string name of an OS configured in both pconfig and oconfig.
        Keyword args:
          - uat_cfg (dict): [None] A dict containing the configuration dict for a UAT or a
            relative path from repo_dir to another config file. If None, tries to load UAT
            from 'uat' field on loaded pconfig
          - override_ip (str): [None] The current IP of the machine to connect to
          - pconfig (str|dict): ['provision.json'] The name of the provisioner file or a dict
          - oconfig (str): ['os.json'] The name of the OS file to be found in repo_dir
        Returns:
            A dict containing the formatted configuration for use by the provisioner
        Raises:
          - ValueError or Exception if invalid config is provided. See errstr for details
        """
        opts = {
            'uat_cfg'   : None,
            'override_ip': None,
            'mac'       : None,
            'pconfig'   : 'provision.json',
            'oconfig'   : 'os.json'
        }
        opts.update(kwargs)
        #val_out = self.validator.provisioner_config(opts['pconfig'])
        #if val_out['errors'] > 0:
        #    raise ValueError('Invalid config provided')

        cfg = self.get_provision_config(pconfig=opts['pconfig'], mac=opts['mac'])
        self.local_filepaths['pconfig'] = f'{self.local_filepaths["repo_dir"]}/{opts["pconfig"]}'
        if 'uat' in cfg and not opts['uat_cfg']:
            opts['uat_cfg'] = self.get_provision_config(pconfig=cfg['uat'])
        if 'local_filepaths' in cfg:
            for lfp in cfg['local_filepaths']:
                if not lfp in self.local_filepaths:
                    self.print(f'Invalid key {lfp} in local_filepaths', level=logging.WARNING)
                    continue
                self.local_filepaths[lfp] = f"{self.local_filepaths['repo_dir']}/{cfg['local_filepaths'][lfp]}"
        if 'remote_filepaths' in cfg:
            for rfp in cfg['remote_filepaths']:
                if not rfp in self.remote_filepaths:
                    self.print(f'Invalid key {rfp} in remote_filepaths', level=logging.WARNING)
                    continue
                self.remote_filepaths[rfp] = cfg['remote_filepaths'][rfp]
        _cfg = dict(cfg)
        # is str, convert to dict
        if isinstance(_cfg['os'], str):
            _cfg['os'] = self.get_os_config(tgt_os=tgt_os, oconfig=_cfg['os'])['os']
        elif isinstance(_cfg['os'], list):
            _cfg['os'] = self.get_os_config(tgt_os=tgt_os,
                                            oconfig=opts['oconfig'],
                                            os_list=_cfg['os'])['os']
        if isinstance(_cfg['os'], dict) and tgt_os:
            _cfg['os']['profile'] = tgt_os
            _cfg['os']['distro'] = _cfg['os']['profile_name']
            _cfg['os']['profile_name'] = f"{_cfg['os']['profile']}-{_cfg['test_target']}"

            if 'extra_lists' in _cfg['os'] and isinstance(_cfg['os']['extra_lists'], dict):
                for field in _cfg['os']['extra_lists']:
                    if not isinstance(_cfg[field], list):
                        self.print(f'{field} is not a list', level=logging.WARNING)
                        continue
                    if field in _cfg:
                        _cfg[field].extend(_cfg['os']['extra_lists'][field])
                    else:
                        _cfg[field] = _cfg['os']['extra_lists'][field]
                del _cfg['os']['extra_lists']

        # update ansible vars
        whitelist_dicts = ['netboot']
        for field in dict(_cfg['os']):
            if not isinstance(_cfg['os'][field], dict) or field in whitelist_dicts:
                continue
            elif field in _cfg:
                _cfg[field] = self.update_dict(_cfg['os'][field], _cfg[field])
            else:
                _cfg[field] = dict(_cfg['os'][field])
            del _cfg['os'][field]

        # if os field is a list of strings, assume oconfig
        if opts['uat_cfg']:
            _cfg['uat'] = opts['uat_cfg']
        if opts['override_ip']:
            _cfg['ip_address'] = opts['override_ip']

        #self.initialize_iboot(_cfg)
        return _cfg

    def get_provision_config(self, **kwargs):
        """
        Fetches the provisioner pseudo-template configuration from a given provisioner config file.

        Keyword args:
          - pconfig (str|dict): ['provision.json'] The name of the provisioner file or a dict
          - mac (str): [None] MAC address to replace in pconfig file
        Returns:
            A dict containing the unformatted provisioner configuration.
        """
        opts = {
            'pconfig'   : 'provision.json',
            'mac'       : None
        }
        opts.update(kwargs)

        cfg = {}
        if isinstance(opts['pconfig'], str):
            with open(f"{self.local_filepaths['repo_dir']}/{opts['pconfig']}", 'r') as pfile:
                data = json.load(pfile)
                cfg = data
            if opts['mac']:
                cfg['mac_address'] = opts['mac']
                with open(f"{self.local_filepaths['repo_dir']}/{opts['pconfig']}", 'w') as pfile:
                    json.dump(cfg, pfile, indent=4)
        elif isinstance(opts['pconfig'], dict):
            # load in config directly
            cfg = opts['pconfig']

        return cfg

    def update_dict(self, dict1, dict2, **kwargs):
        """
        Combines two dicts recursively. Requires that each field in both dicts be of same type.

        Args:
          - d1 (dict): First dict to combine
          - d2 (dict): Second dict to combine
        Keyword args:
          - pref_d2 (bool): [False] If True, use d2 values for non lists and dicts. Else use d1
        Returns:
            The combined dict
        """
        opts = {
            'pref_dict2'    : False
        }
        opts.update(kwargs)

        ret = dict(dict1)
        for field in dict2:
            if field in ret and isinstance(dict2[field], type(ret[field])):
                if isinstance(dict2[field], list):
                    ret[field].extend(dict2[field])
                elif isinstance(dict2[field], dict):
                    ret[field] = self.update_dict(dict2[field], ret[field])
                elif opts['pref_dict2']:
                    ret[field] = dict2[field]
            else:
                ret[field] = dict2[field]
        return ret

    def get_os_config(self, **kwargs):
        """
        Builds the OS level config.

        Keyword args:
          - tgt_os (str): [None] The string name of an OS configured in both pconfig and oconfig.
          - oconfig (str): ['os.json'] The name of the OS file to be found at repo_dir
          - os_list (list): [[]] Allowed OS's if defined in tgt cfg
        Returns:
            A dict containing either the requested OS configuration or the entire oconfig file
        Raises:
            A ValueError if invalid OS is supplied
        """
        opts = {
            'tgt_os'    : None,
            'oconfig'   : 'os.json',
            'os_list'   : []
        }
        opts.update(kwargs)

        cfg = {}

        with open(f"{self.local_filepaths['repo_dir']}/{opts['oconfig']}", 'r') as ofile:
            data = json.load(ofile)
            if not opts['os_list']:
                # no os_list, build it
                for os_type in data:
                    opts['os_list'].extend(list(data[os_type]))
            for os_type in data:
                if opts['tgt_os'] and opts['tgt_os'] in data[os_type]:
                    # save tgt_os and add to config
                    cfg['os'] = data[os_type][opts['tgt_os']]
                    cfg['os']['profile'] = opts['tgt_os']
                    if 'global' in data[os_type]:
                        cfg['os'] = self.update_dict(cfg['os'], data[os_type]['global'])
                    break
                else:
                    cfg['os'] = data
        if opts['tgt_os'] and opts['tgt_os'] not in opts['os_list']:
            raise ValueError(f'Invalid os "{opts["tgt_os"]}" supplied. Valid choices are '
                             f'[{opts["os_list"]}]')
        return cfg

    def check_target_config(self, tgt_cfg, **kwargs):
        """
        Connects to the target machine and compares {Util.remote_filepaths['complete_flag']}
        to {tgt_cfg} file.

        Args:
          - tgt_cfg (dict): The configuration to compare to the installed configuration.
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - client (paramiko.SSHClient): [Util._client] paramiko.SSHClient object to use
        Returns:
            True if installed configuration matches the supplied one, else False
        """
        opts = {
            "quiet"     : False,
            "client"    : self._client
        }
        opts.update(kwargs)

        _tgt_cfg = tgt_cfg

        self.print("Checking current configuration of target...", quiet=opts['quiet'])
        ftp_client = opts['client'].open_sftp()
        if self.remote_filepaths['complete_flag'] in ftp_client.listdir('.'):
            with ftp_client.open(self.remote_filepaths['complete_flag'], 'r') as checkf:
                # compare to current config
                try:
                    ccfg = json.load(checkf)
                    self.print(f"Target machine is configured for {ccfg['os']['profile']}",
                               quiet=opts['quiet'])
                    if ccfg == _tgt_cfg:
                        self.print("To force reinstall, re-run this function with force=True",
                                   quiet=opts['quiet'])
                        return True
                except Exception as exc:
                    self.print(f"!!!{exc}", quiet=opts['quiet'])
                    raise exc
        # default return False aka not configured
        return False

    def set_target_config(self, tgt_cfg, **kwargs):
        """
        Connects to the target machine and sets {Util.remote_filepaths['complete_flag']} to
        {tgt_cfg} file.

        Args:
          - tgt_cfg (dict): The configuration to compare to the installed configuration.
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - client (paramiko.SSHClient): [Util._client] paramiko.SSHClient object to use
        """
        opts = {
            "quiet"     : False,
            "client"    : self._client
        }
        opts.update(kwargs)

        self.print("Copying config to target to mark provisioning as complete...",
                   quiet=opts['quiet'])
        ftp_client = opts['client'].open_sftp()
        _tgt_cfg = tgt_cfg

        with ftp_client.open(self.remote_filepaths['complete_flag'], 'w') as compf:
            json.dump(_tgt_cfg, compf, indent=2)
        ftp_client.chmod(self.remote_filepaths['complete_flag'], 0o644)
        ftp_client.close()
        self.print("Done!", quiet=opts['quiet'])

    def connect(self, tgt_cfg, **kwargs):
        """
        Uses or sets up a client object for connecting to a target machine. Switches based
        on availability of SSH or WinRM on configured target machine.

        Args:
          - tgt_cfg (dict): The configuration to use for the connection.
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - attempts (int): [50] How many times to try the connection before admitting defeat
          - delay (int): [10] How long in seconds to wait between attempts
          - client (paramiko.SSHClient|winrm.Session): [None] A client session object to use
        Returns:
          - The connected paramiko.SSHClient or winrm.Session object
        Raises:
          - ValueError if conn_type is invalid
          - An appropriate error if unable to connect
        """
        opts = {
            'quiet'     : False,
            'attempts'  : 50,
            'delay'     : 10,
            'client'    : self._client
        }
        opts.update(kwargs)

        if isinstance(opts['client'], paramiko.client.SSHClient):
            opts['client'].close()
        opts['client'] = None

        if 'conn_type' not in tgt_cfg or tgt_cfg['conn_type'] == 'ssh':
            ret = self._ssh_connect(tgt_cfg, **opts)
        elif tgt_cfg['conn_type'] == 'winrm':
            ret = self._winrm_connect(tgt_cfg, **opts)
        else:
            raise ValueError(f'conn_type {tgt_cfg["conn_type"]} is not valid.')
        return ret

    def _winrm_connect(self, tgt_cfg, **opts):
        """
        Uses or sets up a winrm.Session object to connect to a target machine and sets
        {Util._client} to the object. Should only be called through Util.connect
        """
        opts['client'] = winrm.Session(
            tgt_cfg['ip_address'],
            auth=(tgt_cfg['dev_username'], tgt_cfg['dev_password'])
            )
        try:
            sysinfo = opts['client'].run_cmd(
                'systeminfo | findstr /B /C:"OS Name" /C:"OS Version"'
                )
            self.print('Printing connected system info:')
            self.print(sysinfo.std_out.decode(), use_logger=False, quiet=opts['quiet'])
            self._client = opts['client']
            return opts['client']
        except requests.exceptions.ConnectionError as conn_exc:
            self.print(str(conn_exc), level=logging.ERROR)
            raise conn_exc

    def _ssh_connect(self, tgt_cfg, **opts):
        """
        Uses or sets up a paramiko.SSHClient object to connect to a target machine and sets
        {Util._client} to the object. Should only be called through Util.connect
        """
        opts['client'] = paramiko.SSHClient()
        opts['client'].set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        opts['client'].load_host_keys('/dev/null')

        _r = 0
        while _r < opts['attempts']:
            try:
                _r += 1
                opts['client'].connect(
                    tgt_cfg['ip_address'],
                    int(tgt_cfg['port']),
                    tgt_cfg['dev_username'],
                    tgt_cfg['dev_password'],
                    timeout=opts['delay']
                )
                self._client = opts['client']
                return opts['client']
            except (
                    paramiko.ssh_exception.NoValidConnectionsError,
                    paramiko.ssh_exception.AuthenticationException,
                    socket.timeout,
                    EOFError
                ) as exc:
                attstr = str(len(str(opts['attempts'])))
                fmtstr = "{: <"+attstr+"}: Failed to connect to {}. Waiting {}s and trying again."
                self.print(fmtstr.format(
                    _r,
                    tgt_cfg['ip_address'],
                    opts['delay']
                ), end='', quiet=opts['quiet'], use_logger=False)
                _d = 0
                while _d < opts['delay']:
                    _d += 1
                    sys.stdout.flush()
                    time.sleep(1)
                    self.print('.', end='', quiet=opts['quiet'], use_logger=False)
                self.print('', quiet=opts['quiet'], use_logger=False)
            if _r >= opts['attempts']:
                break

        raise paramiko.ssh_exception.SSHException("Couldn't reconnect!")

    def reboot(self, tgt_cfg, **kwargs):
        """
        If an iboot is connected and iboot=False is not set, hard reboot the target.
        Otherwise issue a sudo reboot

        Args:
          - tgt_cfg (dict): The configuration to use for the connection.
        Keyword args:
          - iboot (bool): [True] If True, reboot using the iboot's on/off functions
          - no_wait (bool): [False] If true, do not reconnect after sending reboot signal
          - connectargs (dict): [{}] kwargs to pass to connect
        Returns:
          Nothing. Check it yourself.
        """
        opts = {
            'iboot': True,
            'no_wait' : False,
            'connectargs': {}
        }
        opts.update(kwargs)

        self.initialize_iboot(tgt_cfg)
        if opts['iboot'] and self.iboot:
            self.print('Hard rebooting target')
            try:
                self.connect(tgt_cfg, attempts=1, delay=3)
                self.run_command('sudo shutdown now')
            except Exception:
                pass
            self.iboot.off()
            time.sleep(2)
            self.iboot.on()
        else:
            self.connect(tgt_cfg, **opts['connectargs'])
            self.run_command('sudo reboot')
        time.sleep(2)
        if not opts['no_wait']:
            self.connect(tgt_cfg, **opts['connectargs'])

    def run_command(self, cmdstr, **kwargs):
        """
        Connects to the target machine using an appropriate method and runs a supplied
        command there.

        Args:
          - cmdstr (str): The command to run on the machine connected to the client
        Global Keyword args:
          - strict (bool): [False] If True, raise an exception  if command exits with non-zero code
          - quiet (bool): [False] Set to true to hide status messages
          - client (paramiko.SSHClient|winrm.Session): [Util._client] session object to use
          - file (file): [None] if supplied, copy stdout and stderr from command into the file
          - logger (str): [{modulename}.{fnname}.run_command] Logger child string
          - local (bool): [False] Run command from the test host, not from UUT or UAT
        Linux Keyword args:
          - sshopts (dict): [{}] kwargs to be supplied to paramiko.SSHClient.exec_command
          - shell (bool): [False] opens a limited interactive shell. Useful only for debugging
          - stdout (bool): [False] if true, return stdout instead of exit code
        Windows Keyword args:
          - use_ps (bool): [True] Use powershell to run commands instead of cmd
        Returns:
            The exit code of the command
        Raises:
          - Global:
            - RuntimeError if client has not been initialized
          - Linux:
            - paramiko.ssh_exception.SSHException if strict is True and the command fails
          - Windows:
            -
        """
        stack = inspect.stack()[1]
        opts = {
            "strict"    : False,
            "quiet"     : False,
            "client"    : self._client,
            "file"      : None,
            "sshopts"   : {},
            "shell"     : False,
            "logger"    : f'{inspect.getmodulename(stack[1])}.{stack[3]}.run_command',
            "use_ps"    : True,
            "local"     : False,
            "stdout"    : False
        }
        opts.update(kwargs)
        if opts['local']:
            self.print(f"Running '{cmdstr}' locally", quiet=opts['quiet'], logger=opts['logger'])
            return subprocess.call(['/bin/sh', '-c', cmdstr])
        if opts['client']:
            self.print(f"Running '{cmdstr}' remotely", quiet=opts['quiet'], logger=opts['logger'])
            if isinstance(opts['client'], paramiko.client.SSHClient):
                return self._ssh_command(cmdstr, **opts)
            elif isinstance(opts['client'], winrm.Session):
                return self._winrm_command(cmdstr, **opts)
        raise RuntimeError('Client is not initialized!')

    def run_local(self, cmdstr, **kwargs):
        """
        Calls self.local_command with the local=True flag set.

        Takes all the same Keyword Args.
        """
        opts = kwargs
        opts.update({'local':True})
        return self.run_command(cmdstr, **opts)

    def _winrm_command(self, cmdstr, **opts):
        """
        Uses an initialized winrm.Session object (can be generated by running
        `Util.connect`) to run a command via winrm. Do not invoke directly, instead use
        Util.run_command
        """
        output = None
        if not opts['use_ps']:
            output = opts['client'].run_cmd(cmdstr)
            ret = output.status_code
        else:
            try:
                output = opts['client'].run_ps(cmdstr)
                ret = output.status_code
            except TypeError:
                ret = 100
        if isinstance(output, winrm.Response):
            for line in output.std_out.decode().split('\r\n'):
                self.print(line, end='', use_logger=False)
            for line in output.std_err.decode().split('\r\n'):
                self.print(f'stderr: {line}', end='', use_logger=False)
        return ret

    def _ssh_command(self, _cmdstr, **opts):
        """
        Uses an initialized paramiko.SSHClient object (can be generated by running
        `Util.connect`) to run a command via SSH. Do not invoke directly, instead use
        Util.run_command
        """

        cmdstr = f'source /etc/profile && {_cmdstr}'

        if opts['shell']:
            self.print("Opening interactive session", logger=opts['logger'])
            while True:
                try:
                    stdin, stdout, stderr = opts['client'].exec_command(cmdstr)
                    for line in iter(lambda: stdout.readline(), ""):
                        self.print(line, end='', use_logger=False)
                    for line in iter(lambda: stderr.readline(), ""):
                        self.print(f'stderr: {line}', end='', use_logger=False)
                    cmdstr = input('> ')
                except:
                    self.print("\nDone!")
                    break
        else:
            stdin, stdout, stderr = opts['client'].exec_command(cmdstr, **opts['sshopts'])

        buf = ''
        fullbuf = ''
        for line in iter(lambda: stdout.read(5).decode('utf-8',errors='ignore'), ""):
            fullbuf += line
            try:
                if '\n' in line:
                    for _buf in line.split('\n')[0:-1]:
                        buf += _buf
                        self.print(buf, end='\n',
                                   quiet=opts['quiet'],
                                   file=opts['file'],
                                   logger=opts['logger']
                                   )
                        buf = ''
                    buf = line.split('\n')[-1]
                else:
                    buf += line
            except Exception as exc:
                print(exc)
        stdin.close()
        # print stderr
        for line in iter(lambda: stderr.readline(), ""):
            self.print(f'stderr: {line}', end='',
                       quiet=opts['quiet'],
                       file=opts['file'],
                       logger=opts['logger']
                       )
            sys.stdout.flush()
        ret = stdout.channel.recv_exit_status()

        if opts['strict'] and ret != 0:
            raise paramiko.ssh_exception.SSHException(f"'{cmdstr}' failed with code {ret}")
        if opts['stdout']:
            ret = fullbuf

        return ret

    def copy_file(self, loc, rem, **kwargs):
        """
        Connects to the target machine using a paramiko.sftp_client object and copies a file there.

        Args:
          - loc (str): Path to the local file or dir
          - rem (str): Path to copy the local file or dir into
        Keyword args:
          - perm (oct): [None] The permissions to set for the copied file
          - ftp_client (paramiko.sftp_client): [None] paramiko.SFTP_Client to use
          - quiet (bool): [False] Suppress any prints
        Returns:
            The number of files copied.
        """
        opts = {
            'perm'          : None,
            'ftp_client'    : None,
            'quiet'         : False
        }
        opts.update(kwargs)

        ftpflag = False
        if not opts['ftp_client']:
            opts['ftp_client'] = self._client.open_sftp()
            ftpflag = True

        # format r so it doesnt explode
        if not rem.startswith('./') and not rem.startswith('/'):
            rem = f'./{rem}'

        fnum = 0

        # ensure destination dir exists
        crawl = rem.split('/')[0]
        for partpath in rem.split('/')[1:-1]:
            check = f'{crawl}/{partpath}'
            if not partpath in opts['ftp_client'].listdir(crawl):
                self.print(f'Creating {check}', quiet=opts['quiet'])
                opts['ftp_client'].mkdir(check)
            crawl = check

        if os.stat(loc).st_mode & stat.S_IFDIR:
            # its a dir
            if (os.path.basename(rem) in opts['ftp_client'].listdir(os.path.dirname(rem)) and
                    not opts['ftp_client'].stat(rem).st_mode & stat.S_IFDIR):
                errstr = f' {rem} appears to exist and not be a directory.'
                raise Exception(errstr)
            elif not os.path.basename(rem) in opts['ftp_client'].listdir(os.path.dirname(rem)):
                opts['ftp_client'].mkdir(rem)
            for lfile in os.listdir(loc):
                fnum += self.copy_file(f'{loc}/{lfile}', f'{rem}/{lfile}', **opts)

        else:
            # its a file
            self.print(f'Copying "{loc}" => "{rem}"', quiet=opts['quiet'])
            if not opts['perm']:
                perm = (os.stat(loc).st_mode & 0o777)
            else:
                perm = opts['perm']
            opts['ftp_client'].put(loc, rem)
            opts['ftp_client'].chmod(rem, perm)
            fnum = 1

        if ftpflag:
            opts['ftp_client'].close()
        return fnum

    def get_file(self, rem, loc, **kwargs):
        """
        Connects to the target machine using a paramiko.sftp_client object and retrieves a
        file there.

        Args:
          - rem (str): Path to the remote file or dir to copy over
          - loc (str): Path to the local file or dir to copy into
        Keyword args:
          - perm (oct): [None] The permissions to set for the copied file
          - ftp_client (paramiko.sftp_client): [None] paramiko.SFTP_Client to use
          - quiet (bool): [False] Suppress any prints
        Returns:
            The number of files retrieved.
        """
        opts = {
            'perm'          : None,
            'ftp_client'    : None,
            'quiet'         : False
        }
        opts.update(kwargs)

        ftpflag = False
        if not opts['ftp_client']:
            opts['ftp_client'] = self._client.open_sftp()
            ftpflag = True
        fnum = 0
        locdir = '/'.join(loc.split('/')[0:-1])

        # check if r is dir
        try:
            remstat = opts['ftp_client'].stat(rem)
        except IOError as fnfex:
            self.print(f'Failed to get "{rem}" from remote', level=logging.ERROR)
            return -1
        if remstat.st_mode & stat.S_IFDIR:
            # its a dir
            if os.path.exists(loc) and not os.path.isdir(loc):
                errstr = f' {loc} appears to exist and not be a directory.'
                raise Exception(errstr)
            for rfile in opts['ftp_client'].listdir(rem):
                fnum += self.get_file(f'{rem}/{rfile}', f'{loc}/{rfile}', **opts)
        else:
            # its the solo file, snag it
            if not os.path.exists(locdir):
                os.makedirs(locdir)
            self.print(f'Fetching "{loc}" <= "{rem}"', quiet=opts['quiet'])
            if not opts['perm']:
                perm = (opts['ftp_client'].stat(rem).st_mode & 0o777)
            else:
                perm = opts['perm']
            opts['ftp_client'].get(rem, loc)
            os.chmod(loc, perm)
            fnum = 1

        if ftpflag:
            opts['ftp_client'].close()
        return fnum

    def get_local_file(self, rem, loc, **kwargs):
        """
        Copies LocalHost test file

        Args:
          - rem (str): Path to the remote file or dir to copy over
          - loc (str): Path to the local file or dir to copy into
        Keyword args:
          - perm (oct): [None] The permissions to set for the copied file
          - quiet (bool): [False] Suppress any prints
        Returns:
            The number of files retrieved.
        """
        opts = {
            'perm'          : None,
            'quiet'         : False
        }
        opts.update(kwargs)

        fnum = 0
        locdir = '/'.join(loc.split('/')[0:-1])

        # check if r is dir
        try:
            remstat = os.stat(rem)
        except IOError as fnfex:
            self.print(f'Failed to get "{rem}" from localhost', level=logging.ERROR)
            return -1
        if remstat.st_mode & stat.S_IFDIR:
            # its a dir
            if os.path.exists(loc) and not os.path.isdir(loc):
                errstr = f' {loc} appears to exist and not be a directory.'
                raise Exception(errstr)
            for rfile in os.listdir(rem):
                fnum += self.get_local_file(f'{rem}/{rfile}', f'{loc}/{rfile}', **opts)
        else:
            # its the solo file, snag it
            if not os.path.exists(locdir):
                os.makedirs(locdir)
            self.print(f'Fetching "{loc}" <= "{rem}"', quiet=opts['quiet'])
            if not opts['perm']:
                perm = (os.stat(rem).st_mode & 0o777)
            else:
                perm = opts['perm']
            copyfile(rem, loc)
            os.chmod(loc, perm)
            fnum = 1

        return fnum


    def initialize_iboot(self, tgt_cfg, **kwargs):
        """
        Attempts to initialize Util.iboot using the provided config dict.

        Args:
          - tgt_cfg (dict): The configuration to use for the connection.
        Keyword args
          - iboot_cfg (dict): [None] If provided, overrides the configuration from tgt_cfg
          - debug (bool): [False]
        Returns
          False if iboot not configured, True otherwise
        """
        opts = {
            'iboot_cfg' : None,
            'debug' : False
        }
        opts.update(kwargs)
        self.iboot = None
        if 'iboot' not in tgt_cfg:
            if opts['iboot_cfg']:
                tgt_cfg['iboot'] = opts['iboot_cfg']
            else:
                self.print('No iboot config found in configuration!', level=logging.ERROR)
                self.iboot = None
                return False
        try:
            self.iboot = IBoot(tgt_cfg['iboot'], debug=opts['debug'])
        except Exception as exc:
            print(exc)
            self.iboot = None
        return False

    @staticmethod
    def parse_args(args):
        """Create an args dict using argparse"""
        parser = argparse.ArgumentParser()
        for arg in args:
            if args[arg] is None:
                parser.add_argument(arg)
            elif isinstance(args[arg], bool):
                parser.add_argument(f'--{arg}', action='store_true', help=f'[bool] Default: {str(args[arg])}')
            else:
                parser.add_argument(f'--{arg}', type=type(args[arg]), default=args[arg], help=f'[{type(args[arg]).__name__}] Default: {str(args[arg])}')
        return parser.parse_args().__dict__

class IBoot:
    """
    A simple iBoot control module. Member functions use the built-in HTTP API to control
    a configured iBoot module. Should work fine with any iBoot model.

    iBoot config dict is as follows:
    {
        'ip_address'    : '...',
        'user'          : '...',
        'password'      : '...'
    }
    """
    #status = _IBoot_status
    class Status(IntEnum):
        """Status values"""
        OFF = 0
        ON = 1
        QUERY = 2

    # current status
    IB_STATUS = Status.QUERY
    IB_IP = None
    IB_USER = None
    IB_PASS = None
    IB_API = lambda self, **opts: (f'http://{self.IB_IP}?'
                                   f'{"&".join([f"{k}={v}&" for k,v in opts.items()])}'
                                   f'u={self.IB_USER}&p={self.IB_PASS}&c=1')
    debug = False

    def __init__(self, iboot_cfg, **kwargs):
        """
        Loads configuration of a specified iBoot device, identifies its current status,
        and sets the initial status bit.

        Args:
          - iboot_cfg (dict): A dict containing an ip_address, user, and password
        Keyword args:
          - loglevel (logging.LEVEL): [logging.WARNING] loglevel for urllib3
          - debug (bool): [False] If true, print all output. Otherwise, hide all output.
        """
        opts = {
            'loglevel'  : logging.WARNING,
            'debug'     : False
        }
        opts.update(kwargs)
        logging.getLogger('urllib3').setLevel(opts['loglevel'])
        self.IB_IP = iboot_cfg['ip_address']
        self.IB_USER = iboot_cfg['user']
        self.IB_PASS = iboot_cfg['password']
        self.IB_STATUS = self.get_status()
        self.debug = opts['debug']

    def print(self, msg):
        if self.debug:
            print(msg)
        else:
            pass

    def get_status(self):
        """Uses the IBoot web API to return the status bit of the iboot device."""
        xml = minidom.parseString(requests.get(self.IB_API(s=int(self.Status.QUERY)),timeout=10).text)
        self.print(xml.getElementsByTagName('status')[0].firstChild.wholeText.split(',')[0])
        return self.Status[xml.getElementsByTagName('status')[0].firstChild.wholeText.split(',')[0]]

    def on(self):
        """Turns the iboot on via the web API"""
        requests.get(self.IB_API(s=int(self.Status.ON)), timeout=10)
        self.IB_STATUS = self.Status.ON
        time.sleep(1)
        return self.get_status()

    def off(self):
        """
        Turns the iboot off via the web api
        """
        requests.get(self.IB_API(s=int(self.Status.OFF)), timeout=10)
        self.IB_STATUS = self.Status.OFF
        time.sleep(1)
        return self.get_status()

    def toggle(self, **kwargs):
        """
        Toggles the state of the iboot from off->on->off or on->off->on depending
        on the current status.

        Keyword args:
          - duration (int): [5] How long to wait between the toggled states
        """
        opts = {
            'duration'  : 5
        }
        opts.update(kwargs)

        if self.IB_STATUS == self.Status.OFF:
            self.on()
            time.sleep(int(opts['duration']))
            self.off()
        else:
            self.off()
            time.sleep(int(opts['duration']))
            self.on()

def main():
    """main func"""
    args = Util.parse_args({
        'repo_dir'      : os.environ['PWD'],
        'pconfig'       : 'provision.json',
        'cmd'           : 'pwd',
        'force'         : False,
        'iboot'         : False,
        'iboot_cmd'     : ""
    })

    util = Util(repo_dir=args['repo_dir'])
    cfg = util.build_config(None, pconfig=args['pconfig'])
    if not args['iboot'] and not args['iboot_cmd']:
        util.connect(cfg)
        util.run_command(args['cmd'], shell=True)
    else:
        util.initialize_iboot(cfg, debug=True)
        if args['iboot_cmd'] == 'on':
            util.iboot.on()
        elif args['iboot_cmd'] == 'off':
            util.iboot.off()
        elif args['iboot_cmd'] == 'query':
            print(util.iboot.get_status())
        elif args['iboot_cmd'] == 'toggle':
            util.iboot.toggle()
        else:
            print('Valid iboot_cmd\'s are on, off, toggle, and query.')

if __name__ == "__main__":
    main()
