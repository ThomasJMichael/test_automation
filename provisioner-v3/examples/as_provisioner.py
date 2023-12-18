#!/usr/bin/env python3
"""
Attempts to provision a pair of boards, a UAT and a UUT, with specified operating systems.
Also installs all configured dependencies for those Operating Systems.
"""
import os
import sys
import json
import time
import argparse
from aslinuxtester.util import Util
from aslinuxtester.cobbler import Cobbler
from aslinuxtester.dependencies import Dependencies

def parse_args():
    """Creates an argparse dict and returns it"""
    parser = argparse.ArgumentParser()

    # the path to a configuration repo as described in README.md
    parser.add_argument('repo_dir', type=str)
    # an OS defined in both <repo_dir>/os.json and <repo_dir>/provision.json
    parser.add_argument('tgt_os', type=str)
    # an OS defined for the UAT. If undefined, default to first configured OS
    parser.add_argument('--uat_os', type=str)
    # skip provisioning UAT even if its configured
    parser.add_argument('--skip_uat', action='store_true')
    return parser.parse_args().__dict__

def main(args):
    util = Util(args['repo_dir'])
    cblr = Cobbler(util=util)
    dpnd = Dependencies(util=util)

    # Attempt to provision any configured UAT
    try:
        _tmpcfg = util.get_provision_config()['uat']
        if not args['uat_os']:
            args['uat_os'] = _tmpcfg['os'][0]
        uat_cfg = util.build_config(args['uat_os'], pconfig=_tmpcfg)
        del _tmpcfg
    except:
        print("! No valid UAT config found")
        uat_cfg = None

    if uat_cfg and not args['skip_uat']:
        print('UAT Config')
        print(json.dumps(uat_cfg, indent=2))
        print('---------------------')
        input('Press any key to continue: ')
        cblr.provision_system(uat_cfg, force=True)
        # wait for the reboot to happen
        time.sleep(5)
        util.connect(uat_cfg)
        util.run_command('sudo reboot')
        dpnd.install_all(uat_cfg)

    # Provision the requested UUT
    tgt_cfg = util.build_config(args['tgt_os'])
    print('UUT Config')
    print(json.dumps(tgt_cfg, indent=2))
    print('---------------------')
    input('Press any key to continue: ')
    cblr.provision_system(tgt_cfg, force=True)
    # wait for the reboot to happen
    time.sleep(5)
    util.connect(tgt_cfg)
    util.run_command('sudo reboot')
    dpnd.install_all(tgt_cfg)

    pass

if __name__ == "__main__":
    main(parse_args())
