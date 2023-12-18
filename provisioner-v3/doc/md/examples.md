# Example usages  
## [as_provisioner.py](../../examples/as_provisioner.py)  

Attempts to provision a pair of boards, a UAT and a UUT, with specified operating systems.
Also installs all configured dependencies for those Operating Systems.

```python
#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
from aslinuxtester.util import Util
from aslinuxtester.cobbler import Cobbler
from aslinuxtester.dependencies import Dependencies

def parse_args():
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
```

## [as_test_driver.py](../../examples/as_test_driver.py)  

Attempts to provision a pair of boards, a UAT and a UUT, with specified operating systems,
then runs all configured tests on those boards, fetching logs for all failing tests.

```python
#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
from aslinuxtester.util import Util
from aslinuxtester.test import Test
from aslinuxtester.dependencies import Dependencies

def parse_args():
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
```

