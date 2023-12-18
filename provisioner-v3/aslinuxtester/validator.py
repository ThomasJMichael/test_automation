#!/usr/bin/env python3
"""Validates a json configuration file"""
import sys
import os
import json
import logging
try:
    from .util import Util
except ImportError:
    from util import Util

class Validator():
    """
    Validates an osconfig file or a provisioner config file, and creates
    useful lists of the items within.

    Include by doing
    ```python
    from aslinuxtester.validator import Validator
    from aslinuxtester.util import util
    util = Util('/path/to/config/repo')
    validator = Validator(util=util)
    ...
    ```

    To validate a file manually, you can directly run this file like so
    ```bash
    python3 validator.py --repo_dir /path/to/repo/dir
    ```
    """
    def __init__(self, **kwargs):
        """
        If util is supplied at init, set the class-level util to that object.
        Otherwise, requires a repo_dir to initialize a new util.Util

        Keyword args:
          - util (util.Util): [None] A previously initialized util.Util object
          - repo_dir (str): [None] The path to the configuration repository
        Raises:
          - ValueError if neither repo_dir nor util are provided
        """

        opts = {
            'util'      : None,
            'repo_dir'  : None
        }
        opts.update(kwargs)

        if opts['util']:
            self.util = opts['util']
        elif opts['repo_dir']:
            self.util = Util(repo_dir=opts['repo_dir'])
        else:
            raise ValueError("repo_dir is required if util is not provided.")

    def provisioner_config(self, pconfig, **kwargs):
        """
        Validates all optional and required fields for a specified Provisioner Config
        file in repo_dir

        Args:
          - pconfig (str|dict): The provisioner config file to validate
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - verbose (bool): [False] Print INFO messages
        Returns:
          #TODO
        """
        opts = {
            'quiet'     : False,
            'verbose'   : False
        }
        opts.update(kwargs)

        fpath = f'{self.util.local_filepaths["repo_dir"]}/{pconfig}'
        ret = {
            'errors' : 0,
            'warnings' : 0
        }
        required_fields = [
            ('mac_address', str),
            ('ip_address', str),
            ('port', int),
            ('gateway', str),
            ('system_name', str),
            ('dev_username', str),
            ('dev_password', str),
            ('os', [list, dict, str]),
            ('drivers', list)
        ]
        optional_fields = [
            ('conn_type', str, ['ssh', 'winrm']),
            ('ksmeta', dict),
            ('prereqs', list),
            ('postreqs', list),
            ('post_test_scripts', list)
        ]

        try:
            if isinstance(pconfig, str):
                self.util.print(f'Scanning {pconfig} as configured')
                with open(fpath, 'r') as pfile:
                    pcfg = json.load(pfile)
            elif isinstance(pconfig, dict):
                self.util.print('Scanning provisioner config as configured')
                pcfg = pconfig
            else:
                raise ValueError('invalid pconfig')
            # LETS GET TO CHECKIN
            for req_f in required_fields:
                if opts['verbose']:
                    self.util.print(f'Scanning required field {req_f[0]}',
                                    quiet=opts['quiet'],
                                    level=logging.INFO)
                if not req_f[0] in pcfg:
                    # not found
                    self.util.print(
                        f'Required field {req_f[0]} is missing.',
                        level=logging.ERROR,
                        )
                    ret['errors'] += 1
                    continue
                else:
                    if not isinstance(req_f[1], list):
                        types = [req_f[1]]
                    else:
                        types = req_f[1]
                    if not type(pcfg[req_f[0]]) in types:
                        self.util.print(
                            f'{req_f[0]} must be of type {types}',
                            level=logging.ERROR,
                            )
                        ret['errors'] += 1
                if len(req_f) > 2 and not pcfg[req_f[0]] in req_f[2]:
                    self.util.print(
                        f'{req_f[0]} must be one of {req_f[2]}',
                        level=logging.ERROR
                        )
                    ret['errors'] += 1

            # warnings here
            for opt_f in optional_fields:
                if opts['verbose']:
                    self.util.print(f'Scanning optional field {opt_f[0]}',
                                    quiet=opts['quiet'],
                                    level=logging.INFO)
                if not opt_f[0] in pcfg:
                    self.util.print(
                        f'Optional field {opt_f[0]} is missing.',
                        level=logging.WARNING,
                        quiet=opts['quiet'],
                        )
                    ret['warnings'] += 1
                    continue
                else:
                    if not isinstance(req_f[1], list):
                        types = [opt_f[1]]
                    else:
                        types = opt_f[1]
                    if not type(pcfg[opt_f[0]]) in types:
                        self.util.print(
                            f'{opt_f[0]} must be of type {types}',
                            level=logging.ERROR,
                            )
                        ret['errors'] += 1
                    if len(opt_f) > 2 and not pcfg[opt_f[0]] in opt_f[2]:
                        self.util.print(
                            f'{opt_f[0]} must be one of {opt_f[2]}',
                            level=logging.ERROR
                            )
                        ret['errors'] += 1
            if 'test_scripts' in pcfg and isinstance(pcfg['test_scripts'], list):
                test_num = 0
                for test_s in pcfg['test_scripts']:
                    # increment the test_num
                    test_num += 1
                    if not 'name' in test_s:
                        self.util.print(f'Test {test_num} has no name',
                                        level=logging.ERROR)
                        ret['errors'] += 1
                    if not 'repo' in test_s:
                        self.util.print(f'Test {test_num} has no repo',
                                        level=logging.ERROR)
                        ret['errors'] += 1
                    if not 'commands' in test_s:
                        self.util.print(f'Test {test_num} has no commands',
                                        level=logging.ERROR)
                        ret['errors'] += 1
                    elif not isinstance(test_s['commands'], list):
                        self.util.print(f'Test {test_num} commands are not a list',
                                        level=logging.ERROR)
                        ret['errors'] += 1
                    if not 'logs' in test_s:
                        self.util.print(f'Test {test_num} has no logs',
                                        level=logging.ERROR)
                        ret['errors'] += 1
                    if 'type' in test_s and test_s['type'] == 'svn':
                        # svn stuff
                        if not 'svn_user' in test_s:
                            self.util.print(f'svn_user is not set in test {test_num}',
                                            level=logging.ERROR)
                            ret['errors'] += 1
                        if not 'svn_pass' in test_s:
                            self.util.print(f'svn_pass is not set in test {test_num}',
                                            level=logging.ERROR)
                            ret['error'] += 1
                    else:
                        # default to git
                        if not 'branch' in test_s:
                            self.util.print(f'branch is not set in test {test_num}',
                                            level=logging.ERROR)
                            ret['error'] += 1
            if 'uat' in pcfg:
                ret['uat'] = self.provisioner_config(pcfg['uat'], quiet=opts['quiet'])
        except IOError:
            self.util.print(f'Unable to open the provisioner configuration at {fpath}',
                            level=logging.ERROR)
            ret['errors'] = 255
        except Exception as exc:
            self.util.print(f'Unhandled error: {exc}',
                            level=logging.ERROR)
            ret['errors'] = 255
        return ret

    def os_config(self, oconfig, **kwargs):
        """
        Validates all optional and required fields for a specified OS Config
        file in repo_dir

        Args:
          - oconfig (str): The provisioner config file to validate
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - verbose (bool): [False] Print INFO messages
        Returns:
          #TODO
        """
        opts = {
            'quiet'     : False,
            'verbose'   : False
        }
        opts.update(kwargs)

        ret = {
            'errors' : 0,
            'warnings' : 0
        }
        os_types = [
            'linux',
            'windows'
        ]
        os_fields = [
            ('path', str),
            ('kickstart', str),
            ('profile_name', str),
            ('os_type', str, ['linux', 'windows'])
        ]
        global_fields = [
            ('repos', list),
            ('packages', list)
        ]
        # parse it
        try:
            if isinstance(oconfig, str):
                fpath = f'{self.util.local_filepaths["repo_dir"]}/{oconfig}'
                self.util.print(f'Scanning {oconfig} as configured')
                with open(fpath, 'r') as pfile:
                    ocfg = json.load(pfile)
            elif isinstance(oconfig, dict):
                self.util.print('Scanning OS config as configured')
                ocfg = oconfig
            else:
                raise ValueError('invalid oconfig')
            for os_type in os_types:
                if os_type not in ocfg:
                    if opts['verbose']:
                        self.util.print(f'OS type {os_type} not configured',
                                        level=logging.INFO,
                                        quiet=opts['quiet'])
                    continue
                for osname in ocfg[os_type]:
                    os = ocfg[os_type][osname]
                    if opts['verbose']:
                        self.util.print(f'Scanning field {osname}',
                                        level=logging.INFO,
                                        quiet=opts['quiet'])
                    if not osname == 'global':
                        for os_f in os_fields:
                            if not os_f[0] in os:
                                # not found
                                self.util.print(
                                    f'Required field {os_f[0]} is missing.',
                                    level=logging.ERROR,
                                    )
                                ret['errors'] += 1
                                continue
                            else:
                                if not isinstance(os_f[1], list):
                                    types = [os_f[1]]
                                else:
                                    types = os_f[1]
                                if not type(os[os_f[0]]) in types:
                                    self.util.print(
                                        f'{os_f[0]} must be of type {types}',
                                        level=logging.ERROR,
                                        )
                                    ret['errors'] += 1
                            if len(os_f) > 2 and not os[os_f[0]] in os_f[2]:
                                self.util.print(
                                    f'{os_f[0]} must be one of {os_f[2]}',
                                    level=logging.ERROR
                                    )
                                ret['errors'] += 1
                    for glob_f in global_fields:
                        if not glob_f[0] in os:
                            # not found
                            self.util.print(
                                f'Required field {glob_f[0]} is missing.',
                                level=logging.ERROR,
                                )
                            ret['errors'] += 1
                            continue
                        else:
                            if not isinstance(glob_f[1], list):
                                types = [glob_f[1]]
                            else:
                                types = glob_f[1]
                            if not type(os[glob_f[0]]) in types:
                                self.util.print(
                                    f'{glob_f[0]} must be of type {types}',
                                    level=logging.ERROR,
                                    )
                                ret['errors'] += 1
                        if len(glob_f) > 2 and not os[glob_f[0]] in glob_f[2]:
                            self.util.print(
                                f'{glob_f[0]} must be one of {glob_f[2]}',
                                level=logging.ERROR
                                )
                            ret['errors'] += 1
        except IOError:
            self.util.print(f'Unable to open the OS configuration at {fpath}',
                            level=logging.ERROR)
            ret['errors'] = 255
        except Exception as exc:
            self.util.print(f'Unhandled error: {exc}',
                            level=logging.ERROR)
            ret['errors'] = 255
        return ret

if __name__ == "__main__":
    ARGS = Util.parse_args({
        'repo_dir'      : os.environ['PWD'],
        'pconfig'       : 'provision.json',
        'oconfig'       : 'os.json',
        'verbose'       : False
    })

    VAL = Validator(repo_dir=ARGS['repo_dir'])
    print(json.dumps(VAL.provisioner_config(ARGS['pconfig'], verbose=ARGS['verbose']), indent=2))
    print(json.dumps(VAL.os_config(ARGS['oconfig'], verbose=ARGS['verbose']), indent=2))
