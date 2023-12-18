#!/usr/bin/env python3
"""
Attempts to provision a pair of boards, a UAT and a UUT, with specified operating systems,
then runs all configured tests on those boards, fetching logs for all failing tests.
"""
import os
import sys
import json
import time
import argparse
from aslinuxtester.util import Util
from aslinuxtester.test import Test
from aslinuxtester.dependencies import Dependencies

def parse_args():
    """Creates an argparse dict and returns it"""
    parser = argparse.ArgumentParser()

    # the path to a configuration repo as described in README.md
    parser.add_argument('repo_dir', type=str)
    # an OS defined in both <repo_dir>/os.json and <repo_dir>/provision.json
    parser.add_argument('tgt_os', type=str)
    return parser.parse_args().__dict__

def main(args):
    util = Util(args['repo_dir'])
    dpnd = Dependencies(util=util)
    test = Test(util=util)

    tgt_cfg = util.build_config(args['tgt_os'])
    dpnd.install_all(tgt_cfg, force=True)
    results = test.all_tests(tgt_cfg, fetch_logs=False)

    logbase = util.local_filepaths['logs']
    for testname in results:
        for command in results[testname]:
            print(f'{command} -> {results[testname][command]}')
            if not results[testname][command] == 0:
                util.local_filepaths['logs'] = f'{logbase}/{command.split(" ")[0]}'
                print(test.fetch_logs(tgt_cfg, testname))

if __name__ == "__main__":
    main(parse_args())
