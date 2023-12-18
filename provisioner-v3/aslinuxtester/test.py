#!/usr/bin/env python3
"""The big test Poobah"""
try:
    from .util import Util
except ImportError:
    from util import Util
import sys
import os
import json
import subprocess

class Test():
    """
    Starts, watches, and logs tests, as well as orchestrating post-test scripts

    Include by doing
    ```python
    from aslinuxtester.test import Test
    from aslinuxtester.util import Util
    util = Util('/path/to/config/repo')
    test = Test(util=util)
    ...
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

    def all_tests(self, tgt_cfg, **kwargs):
        """
        Iterates across the configured test objects form the config file and
        amalgamates the results into a single dict with the following structure:

        {
            'test_name1' : {
                'good_command param1 param2' : 0,
                'bad_command param1 param2' : 1
            },
            'test_name2' : {...}
        }

        Args:
          - tgt_cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - post_test_scripts (bool): [False] Whether to run post-test scripts
            automatically after tests have finished
          - fetch_logs (bool): [True] Automatically retrieve logs after running tests
          - path (str): [''] Copy path to send over to fetch_logs
          - quiet (bool): [False] Set to true to hide status messages
        Returns:
            A dict of all test return codes indexed by test name
        """
        opts = {
            'post_test_scripts' : False,
            'fetch_logs'        : True,
            'path'              : '',
            'quiet'             : False
        }
        opts.update(kwargs)
        if "post_test_scripts" in tgt_cfg:
            opts['post_test_scripts'] = True
        self.util.connect(tgt_cfg)
        res = {}
        for test_data in tgt_cfg['test_scripts']:
            res[test_data['name']] = self.run_test(
                tgt_cfg,
                test_data['name'],
                quiet=opts['quiet'],
                fetch_logs=opts['fetch_logs'],
                path=opts['path']
                )
        if opts['post_test_scripts']:
            self.run_post_test_scripts(tgt_cfg)
        return res

    def run_test(self, tgt_cfg, test_name, **kwargs):
        """
        Clones the test repo, iterates across test commands, and formats the exit
        codes into a dict with the following structure:

        {
            'good_command param1 param2': 0,
            'bad_command param1 param2' : 1
        }

        Args:
          - tgt_cfg (dict): The configuration of the target from Util.build_config
          - test_name (str): The name of the test to run from provision.json
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - path (str): [''] Copy path to send over to fetch_logs
          - fetch_logs (bool): [True] Automatically retrieve logs after running test
        Returns:
            A dict of all test command exit codes
        """
        opts = {
            'fetch_logs'    : True,
            'path'          : '',
            'quiet'         : False
        }
        opts.update(kwargs)
        # find test in list
        for _test in tgt_cfg['test_scripts']:
            if _test['name'] == test_name:
                test_data = _test
                break

        if 'use_host_as_uat' in test_data and test_data['use_host_as_uat']:

            opts.update({'path' : f'{self.util.local_filepaths["host_logs"]}'})
            self.util.run_local((f'sudo rm -rf {self.util.local_filepaths["tests"]}/'
                                 f'{test_data["name"]}'
                                 ), quiet=opts['quiet'], logger='test')
            if 'type' in test_data and test_data['type'] == 'svn':
                self.util.run_local((f'svn export {test_data["repo"]} '
                                     f'{self.util.local_filepaths["tests"]}/'
                                     f'{test_data["name"]} '
                                     f'--username {test_data["svn_user"]} '
                                     f'--password {test_data["svn_pass"]} '
                                     ), quiet=opts['quiet'], logger='test')
            else:
                # default to git
                self.util.run_local((f'git clone -b {test_data["branch"]} {test_data["repo"]} '
                                       f'{self.util.local_filepaths["tests"]}/'
                                       f'{test_data["name"]}'
                                       ), quiet=opts['quiet'], logger='test')


            test_res = {}
            for command in test_data['commands']:
                test_res[command] = self.util.run_local(
                    (f'cd {self.util.local_filepaths["tests"]}/{test_data["name"]} '
                     f'&& bash -c "{command}"'), quiet=opts['quiet'], logger=f'test.run_test({test_name})')
            if opts['fetch_logs']:
                self.fetch_logs(tgt_cfg, test_name, path=opts['path'], quiet=opts['quiet'])
            return test_res
        else:
            self.util.connect(tgt_cfg, quiet=opts['quiet'])
            self.util.run_command((f'sudo rm -rf $HOME/{self.util.remote_filepaths["tests"]}/'
                                   f'{test_data["name"]}'
                                   ), quiet=opts['quiet'], logger='test')
            if 'type' in test_data and test_data['type'] == 'svn':
                self.util.run_command((f'svn export {test_data["repo"]} '
                                       f'$HOME/{self.util.remote_filepaths["tests"]}/'
                                       f'{test_data["name"]} '
                                       f'--username {test_data["svn_user"]} '
                                       f'--password {test_data["svn_pass"]} '
                                       ), quiet=opts['quiet'], logger='test')
            else:
                # default to git
                self.util.run_command((f'git clone -b {test_data["branch"]} {test_data["repo"]} '
                                       f'$HOME/{self.util.remote_filepaths["tests"]}/'
                                       f'{test_data["name"]}'
                                       ), quiet=opts['quiet'], logger='test')
            test_res = {}
            for command in test_data['commands']:
                test_res[command] = self.util.run_command(
                    (f'cd $HOME/{self.util.remote_filepaths["tests"]}/{test_data["name"]} '
                     f'&& bash -c "{command}"'), quiet=opts['quiet'], logger=f'test.run_test({test_name})')
            if opts['fetch_logs']:
                self.fetch_logs(tgt_cfg, test_name, path=opts['path'], quiet=opts['quiet'])
            return test_res

    def fetch_logs(self, tgt_cfg, test_name, **kwargs):
        """
        Fetches the logs for a test and copies them to the currently set local log
        directory.

        NOTE: If no logs are found, this won't tell you.

        Args:
          - tgt_cfg (dict): The configuration of the target from Util.build_config
          - test_name (str): The name of the test to fetch logs for from provision.json
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
          - path (str): [{test_name}] Copy path within local_filepaths['logs']
          - compress (bool): [False] Set to true to enable log compression before copying
          - archive (str): [logs.targ.gz] If compress is set to True, the name of the archive
        Returns:
            The directory where the logs were copied to
        """
        # find test in list
        for _test in tgt_cfg['test_scripts']:
            if _test['name'] == test_name:
                test_data = _test
                break
        opts = {
            'quiet'     : False,
            'path'      : f'{test_name}',
            'compress'  : False,
            'archive'   : 'logs.tar.gz'
        }
        opts.update(kwargs)

        self.util.connect(tgt_cfg, quiet=opts['quiet'])

        print(test_data)
        if 'use_host_as_uat' in test_data and test_data['use_host_as_uat']:
            print("Locally fetching")
            remdir =  f'{self.util.local_filepaths["tests"]}/{test_data["name"]}/{test_data["logs"]}'

            locdir = f'{self.util.local_filepaths["logs"]}/{test_data["name"]}'
            print(locdir)
            if opts['compress']:
                self.util.run_command(f'cd {remdir} && tar cpvf {opts["archive"]} .',
                                      strict=True,
                                      quiet=True
                                      )
                rempath = f'{remdir}/{opts["archive"]}'
                locpath = f'{locdir}/{opts["archive"]}'
            else:
                rempath = remdir
                locpath = locdir

            if self.util.get_local_file(rempath, locpath, quiet=opts['quiet']) < 0:
                self.util.print('Failed to fetch logs! Exiting with error.', level=self.util.logging.ERROR)
                exit(-1)
            return locpath
        else:
            remdir = f'{self.util.remote_filepaths["tests"]}/{test_data["name"]}/{test_data["logs"]}'

            locdir = f'{self.util.local_filepaths["logs"]}/{opts["path"]}'
            if opts['compress']:
                self.util.run_command(f'cd {remdir} && tar cpvf {opts["archive"]} .',
                                      strict=True,
                                      quiet=True
                                      )
                rempath = f'{remdir}/{opts["archive"]}'
                locpath = f'{locdir}/{opts["archive"]}'
            else:
                rempath = remdir
                locpath = locdir

            if self.util.get_file(rempath, locpath, quiet=opts['quiet']) < 0:
                self.util.print('Failed to fetch logs! Exiting with error.', level=self.util.logging.ERROR)
                exit(-1)
            return locpath

    def run_post_test_scripts(self, tgt_cfg, **kwargs):
        """
        Runs any configured post test scripts on the test host machine, not the UUT or UAT.
        Useful for uploading logs or cleaning up the working area on the master.

        Args:
          - tgt_cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
        """
        opts = {
            'quiet' : False
        }
        opts.update(kwargs)

        if 'post_test_scripts' not in tgt_cfg:
            self.util.print('No configured post_test_scripts list', quiet=opts['quiet'])
        else:
            for cmd in tgt_cfg['post_test_scripts']:
                cmdstr = f'{self.util.local_filepaths["posttestscripts"]}/{cmd}'
                subprocess.call(['/bin/sh', '-c', cmdstr])

def main():
    ARGS = Util.parse_args({
        'repo_dir'      : os.environ['PWD'],
        'pconfig'       : 'provision.json',
        'override_ip'   : '',
        'tgt_os'        : None,
        'force'         : False,
        'quiet'         : False,
        'test_name'     : ''
    })

    TEST = Test(repo_dir=ARGS['repo_dir'])
    CFG = TEST.util.build_config(
        pconfig=ARGS['pconfig'],
        tgt_os=ARGS['tgt_os'],
        override_ip=ARGS['override_ip'],
        quiet=ARGS['quiet']
    )
    print(json.dumps(CFG, indent=2))
    print('=============')
    sys.stdout.flush()

    try:
        PATH = (f'uut_{CFG["os"]["profile_name"]}_uat'
                      f'-{CFG["uat"]["os"]["profile_name"]}')
    except:
        PATH = f'uut_{CFG["os"]["profile_name"]}'

    RETVAL = 0
    if not ARGS['test_name']:
        RESULTS = TEST.all_tests(CFG, path=PATH)
        print(json.dumps(RESULTS, indent=2))

        for TEST in RESULTS:
            for CMD in RESULTS[TEST]:
                RETVAL = RETVAL + RESULTS[TEST][CMD]
    else:
        RESULTS = TEST.run_test(CFG, ARGS['test_name'], path=PATH)
        print(json.dumps(RESULTS), indent=2)

    exit(RETVAL)

if __name__ == "__main__":
    main()
