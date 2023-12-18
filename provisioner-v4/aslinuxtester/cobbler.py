#!/usr/bin/env python3
"""Local cobbler server controller for use by provisioner"""
import sys
import time
import json
import os
import random
import string
import subprocess
import shutil
try:
    from .util import Util
except ImportError:
    from util import Util

class Cobbler():
    """
    Controls cobbler operations on the test master, including:
    - Distro imports
    - Profile naming
    - System creation

    Include by doing
    ```python
    from aslinuxtester.cobbler import Cobbler
    from aslinuxtester.util import Util
    util = Util('/path/to/config/repo')
    cblr = Cobbler(util=util)
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
          - quiet (bool): [False] Shut it up you
          - debug (bool): [False] Enable debug prints
        Raises:
          - ValueError if neither repo_dir nor util are provided
        """

        opts = {
            'util'      : None,
            'repo_dir'  : None,
            'quiet'     : False,
            'debug'     : False
        }
        opts.update(kwargs)

        if opts['util']:
            self.util = opts['util']
        elif opts['repo_dir']:
            self.util = Util(repo_dir=opts['repo_dir'], quiet=opts['quiet'])
        else:
            raise ValueError("repo_dir is required if util is not provided.")

    ################### FUNCTION DEFS #########################
    def subproc_print(self, p, **kwargs):
        """
        Prints further detail if debug set
        Args:
          - p: Process
        Keyword args:
        - debug (bool): [False] Enable debug prints
        """
        opts = {
            'debug'     : False
        }
        opts.update(kwargs)
	
        if opts['debug']:	
            self.util.print(f'stdout: {p.stdout.decode()}')
            self.util.print(f'exit status: {p.returncode}') 

    def provision_system(self, config, **kwargs):
        """
        Checks the local cobbler server for the OS specified in config, and attempts to
        import the OS if possible. If that is successful, creates a cobbler system and
        sets it to boot the selected OS on reboot.

        Args:
          - config (dict): A formatted configuration dict from util.Util.build_config
        Keyword args:
          - force (bool): [False] Ignore already installed configuration and force creation
          - reload (bool): [False] Reload OS and configuration from os.json
          - quiet (bool): [False] Suppress status messages
          - debug (bool): [False] Enable debug prints
        Raises:
          - SystemError if cobbler failed to import the requested OS or the system could
            not be added
          - TypeError if an invalid OS configuration is provided
        Returns:
            True if reboot is needed to finish provisioning, False if not
        """
        opts = {
            'force'     : False,
            'reload'    : False,
            'quiet'     : False,
            'debug'     : False
        }
        opts.update(kwargs)

        if not isinstance(config['os'], dict):
            raise TypeError(("config['os'] must be a full dictionary defining the target,"
                             "try running the name of the OS thru Util.get_os_config."))
        if opts['reload']:
            self.remove_system(config['system_name'], **opts)
            if not self.remove_profile(config['os'], **opts):
                raise SystemError(
                    f"Could not delete cobbler profile named {config['os']['profile']}."
                    )
        if not self.create_profile_if_missing(config, **opts):
            raise SystemError(
                f"Could not find or create a cobbler profile named {config['os']['profile']}."
                )

        self.util.print(f"Provisioning {config['system_name']}...")
        sys.stdout.flush()
        if 'ksmeta' in config:
            ks_meta = ' '.join(['{}={}'.format(ksm, config['ksmeta'][ksm]) for ksm in config['ksmeta']])
        else:
            ks_meta = ''
        kopts_def = f'inst.ks.device={config["netdev"]} console=tty0 console=ttyS0,115200,8,n,1'
        if 'kopts' in config:
            config['kopts'] = kopts_def + ' ' + config['kopts']
            self.util.print("Kopts exteneded: " + config['kopts']) 
        else:
            config['kopts'] = kopts_def
        config['kopts_post'] = config['kopts']
        if 'nfsroot' in config:
            config['kopts_post'] = f'{config["kopts"]} nfsroot={config["nfsroot"]}'
        env_data = {
            "SYSTEM_NAME"   : config['system_name'],
            "PROFILE"       : config['os']['profile'],
            "MAC_ADDRESS"   : config['mac_address'],
            "NETDEV"        : config['netdev'],
            "IP_ADDRESS"    : config['ip_address'],
            "GATEWAY"       : config['gateway'],
            "DEV_USERNAME"  : config['dev_username'],
            "DEV_PASSWORD"  : config['dev_password'],
            "KOPTS"         : config['kopts'],
            "KOPTS_POST"    : config['kopts_post'],
            "KSMETASTRING"  : (
                f'dev_username={config["dev_username"]} '
                f'dev_password={config["dev_password"]} '
                f'{ks_meta}'
                )
        }
        if self.add_system_ported_from_script(env_data, **opts) != 0:
            self.util.print(" Unable to add system to cobbler!", quiet=opts['quiet'])
            raise SystemError('Cobbler failure!')
        self.util.print(" Done!")
        sys.stdout.flush()
        return True

    def remove_system(self, system_name, **kwargs):
        """
        This was originally a shell script that was called from a Jenkins server
        running on the cobbler host. Manipulated the cobbler server directly
        via subprocess and sets up the new cobbler system.

        Args:
          - system_name (str): Name for the system in cobbler
        Keyword args:
          - quiet (bool): [False] Suppress status messages
        """
        opts = {
            'quiet' : False,
            'debug' : False
        }
        opts.update(kwargs)

        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE
        p = subprocess.run([
                '/bin/sh', '-c',
                f'sudo docker exec  cobbler_container cobbler system report --name {system_name}'
        ], stdout=sbp_stdout)
        self.subproc_print(p, **opts)
        if 'No profile found' in p.stdout.decode():
            self.util.print(f'System {system_name} does not exist',
                            quiet=opts['quiet'])
        else:
            self.util.print(f'System {system_name} already exists, deleting...',
                            quiet=opts['quiet'])
            p = subprocess.run([
                '/bin/sh', '-c',
                f'sudo docker exec  cobbler_container cobbler system remove --name={system_name}'
            ], stdout=sbp_stdout)
            self.subproc_print(p, **opts)

    def add_system_ported_from_script(self, env, **kwargs):
        """
        This was originally a shell script that was called from a Jenkins server
        running on the cobbler host. Manipulated the cobbler server directly
        via subprocess and sets up the new cobbler system.

        Args:
          - env (dict): All the required environment variables needed to tickle cobbler
             + SYSTEM_NAME     : Name for the system in cobbler
             + PROFILE         : Profile to attach to the new system
             + MAC_ADDRESS     : MAC of the interface that will be PXE booting
             + NETDEV          : Network interface that will be PXE booting
             + IP_ADDRESS      : Static IP to assign to the system
             + GATEWAY         : The IP of the cobbler server visible to the system
             + DEV_USERNAME    : User to create on the system
             + DEV_PASSWORD    : Password for $DEV_USERNAME
             + KOPTS           : Kernel options to pass to cobbler.
             + KOPTS_POST      : Kernel options to pass to cobbler.
             + KSMETASTRING    : Additional kickstart variables to supply to cobbler
        Keyword args:
          - quiet (bool): [False] Suppress status messages
          - debug (bool): [False] Print debug messages
        Returns
            0 if successful, else non-zero
        """
        opts = {
            'quiet' : False,
            'debug' : False
        }
        opts.update(kwargs)

        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE

        self.remove_system(env['SYSTEM_NAME'], **opts)

        cmdstr = (f'sudo docker exec  cobbler_container cobbler system add --name="{env["SYSTEM_NAME"]}" '
                  f'--profile="{env["PROFILE"]}"')
        self.util.print(f'Running {cmdstr}', quiet=opts['quiet'])
        p = subprocess.run(['/bin/sh', '-c', cmdstr], stdout=sbp_stdout)
        self.subproc_print(p, **opts)
        cmdstr = (
            f'sudo docker exec  cobbler_container cobbler system edit --name="{env["SYSTEM_NAME"]}" '
            f'--mac="{env["MAC_ADDRESS"]}" --ip-address="{env["IP_ADDRESS"]}" '
            f'--netmask="255.255.255.0" --static=1 --dns-name="{env["SYSTEM_NAME"]}" '
            f'--interface="{env["NETDEV"]}" --gateway="{env["GATEWAY"]}" '
            f'--netboot-enabled=true '
            f'--hostname="{env["SYSTEM_NAME"].replace("_", "-")}" '
            f'--kernel-options="{env["KOPTS"]}" '
            f'--kernel-options-post="{env["KOPTS_POST"]}" '
            f'--filename="grub/grubx64.efi" '
            f'--autoinstall-meta="{env["KSMETASTRING"]}" '
            )
        self.util.print(f'Running {cmdstr}', quiet=opts['quiet'])

        p = subprocess.run([
                '/bin/sh', '-c',
                cmdstr
        ], stdout=sbp_stdout)
        self.subproc_print(p, **opts)
        if p.returncode == 0:
            p = subprocess.run(['/bin/sh', '-c', 'sudo docker exec  cobbler_container cobbler sync'], stdout=sbp_stdout)
            self.subproc_print(p, **opts)
            p = subprocess.run([
                'sudo', 'docker', 'exec', 'cobbler_container', 'cobbler', 'system', 'report', '--name', env['SYSTEM_NAME']
                ], stdout=sbp_stdout)
            self.subproc_print(p, **opts)
            return_val = p.returncode
        else:
            return_val = 1
        p = subprocess.run(['/bin/sh', '-c', 'sudo docker exec  cobbler_container cobbler list'], stdout=sbp_stdout)
        self.util.print(f'{p.stdout.decode()}')
        return return_val

    def remove_profile(self, osconfig, **kwargs):
        """
        Args:
          - osconfig (dict): Just the 'os' config field from util.Util.build_config
        Keyword args:
          - quiet (bool): [False] Suppress status messages
          - debug (bool): [False] Print debug messages
        Raises:
        Returns:
            True if successful, else False
        """
        opts = {
            'quiet' : False,
            'debug' : False
        }
        opts.update(kwargs)
        self.util.print(f'Remove Profile {osconfig["profile"]}.')

        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE
        p = subprocess.run([
            '/bin/sh', '-c', f'sudo docker exec  cobbler_container cobbler profile report --name {osconfig["profile"]}'
        ], stdout=sbp_stdout)
        self.subproc_print(p, **opts)
        if 'No profile found' in p.stdout.decode():
            self.util.print(f'Profile {osconfig["profile"]} does not exist.')
            return True

        cmd = f'sudo docker exec  cobbler_container cobbler profile remove --name {osconfig["profile"]}'
        p = subprocess.run(['/bin/sh', '-c', cmd], stdout=sbp_stdout)
        self.subproc_print(p, **opts)
        if p.returncode != 0:
            self.util.print(f'Failed to run {cmd}')
            return False

        self.util.print(f'Remove Distro {osconfig["distro"]-x86_64}.')
        cmd = f'sudo docker exec  cobbler_container cobbler distro remove --name {osconfig["distro"]}-x86_64'
        p = subprocess.run(['/bin/sh', '-c', cmd], stdout=sbp_stdout)
        self.subproc_print(p, **opts)
        if p.returncode != 0:
            self.util.print(f'Failed to run {cmd}')
            return False

        return True

    def create_profile_if_missing(self, tgt_cfg, **kwargs):
        """
        Checks the local cobbler server for the OS specified in config, and attempts to
        import the OS if possible.

        Args:
          - osconfig (dict): Just the 'os' config field from util.Util.build_config
        Keyword args:
          - quiet (bool): [False] Suppress status messages
          - debug (bool): [False] Print debug messages
        Raises:
          - IOError if supplied with an invalid filepath for an ISO to import
        Returns:
            True if successful, else False
        """
        opts = {
            'quiet' : False,
            'debug' : False
        }
        opts.update(kwargs)
        osconfig = tgt_cfg['os']
        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE

        # check existing profiles for a match
        self.util.print(f'Checking profile {osconfig["profile"]}', quiet=opts['quiet'])
        p = subprocess.run([
            '/bin/sh', '-c', f'sudo docker exec  cobbler_container cobbler profile report --name {osconfig["profile"]}'
        ], stdout = sbp_stdout)
        self.subproc_print(p, **opts)
        if 'No profile found' not in p.stdout.decode():
            self.util.print(f'Profile exists {osconfig["profile"]}', quiet=opts['quiet'])
            return True
        else:
            self.util.print(f'Profile does not exist {osconfig["profile"]}', quiet=opts['quiet'])

        # its go time
        ret = True
        # This checked if the iso was on the host machine. This does not matter since we are mounting inside the conatiner
       # if not os.path.isfile(osconfig['path']):
       #     raise IOError(f"Invalid path to iso '{osconfig['path']}'")

        mntpath = f'/mnt/cobbler.'+''.join(
            random.choices(string.ascii_uppercase + string.digits, k=3)
            )
        self.util.print(f'Mounting inside docker {osconfig["path"]} -> {mntpath}', quiet=opts['quiet'])
        try:

            # detect distro, if not found import fresh
            self.util.print(f'Looking for existing distro {osconfig["profile"]}-x86_64')
            p = subprocess.run([
                '/bin/sh', '-c', f'sudo docker exec  cobbler_container cobbler distro report --name {osconfig["profile"]}-x86_64'
            ], stdout = sbp_stdout)
            self.subproc_print(p, **opts)
            if 'No distro found' in p.stdout.decode():
                try:
                    self.util.print(f'Create folder {mntpath}')
                    subprocess.run(['sudo', 'docker', 'exec', 'cobbler_container', 'mkdir', '-p', mntpath], check=True)
                    # mount the iso
                    self.util.print(f'mntpath {mntpath}')
                    subprocess.run(['sudo', 'docker', 'exec', 'cobbler_container', 'mount', osconfig['path'], mntpath], check=True)
                    # import the iso
                    self.util.print('Importing distro')
                    subprocess.run(['/bin/sh', '-c',
                                    (
                                        f'sudo docker exec  cobbler_container cobbler import --name={osconfig["distro"]} '
                                        f'--path={mntpath}'
                                    )
                                    ], check=True, stdout=sbp_stdout)
                except Exception as exc:
                    self.util.print('That didn\'t work. Failing out...', quiet=opts['quiet'])
                    self.util.print(exc, quiet=opts['quiet'])
                    return False
                finally:
                    # unmount the iso
                    subprocess.run(['sudo', 'docker', 'exec', 'cobbler_container', 'umount', mntpath], stdout=subprocess.DEVNULL)
                # Add tree
                self.util.print('Add tree metadata')
                p = subprocess.run(['/bin/sh', '-c',
                                (
                                    f'sudo docker exec  cobbler_container cobbler distro edit --name={osconfig["distro"]}-x86_64 '
                                    f'--autoinstall-meta="tree=http://@@http_server@@/cblr/links/{osconfig["distro"]}-x86_64" '
                                )
                                ], check=True, stdout=sbp_stdout)
                self.subproc_print(p, **opts)
                self.util.print('Distro Report')
                p = subprocess.run(['/bin/sh', '-c',
                                (
                                    f'sudo docker exec  cobbler_container cobbler distro report --name={osconfig["distro"]}-x86_64 '
                                )
                                ], check=True, stdout=sbp_stdout)
                self.subproc_print(p, **opts)
                self.util.print('Profile Report')
                p = subprocess.run(['/bin/sh', '-c',
                                (
                                    f'sudo docker exec  cobbler_container cobbler profile report --name={osconfig["distro"]}-x86_64 '
                                )
                                ], check=True, stdout=sbp_stdout)
                self.subproc_print(p, **opts)
                # delete and recreate the profile
                self.util.print('Removing new profile')
                p = subprocess.run(['/bin/sh', '-c',
                                f'sudo docker exec  cobbler_container cobbler profile remove --name={osconfig["distro"]}-x86_64'
                                ], check=True, stdout=sbp_stdout)
                self.subproc_print(p, **opts)
            else:
                self.util.print('Distro found in cobbler')

            # load in the kickstart
            self.util.print('Assigning kickstart file - copy from {self.util.local_filepaths["repo_dir"]}')
            ksfile = f'/var/lib/cobbler/templates/{osconfig["profile"]}.ks'
            subprocess.run(['sudo',
                            'docker', 'exec', 'cobbler_container',
                            'cp',
                            f'/tmp/{osconfig["kickstart"]}',
                            ksfile
                            ], check=True, stdout=sbp_stdout)
            self.util.print('Creating new profile')
            subprocess.run(['/bin/sh', '-c',
                            (
                                f'sudo docker exec  cobbler_container cobbler profile add --name={osconfig["profile"]} '
                                f'--distro={osconfig["distro"]}-x86_64 '
                                f'--autoinstall={osconfig["profile"]}.ks'
                            )
                            ], check=True, stdout=sbp_stdout)
            self.util.print('Profile Report')
            p = subprocess.run(['/bin/sh', '-c',
                            (
                                f'sudo docker exec  cobbler_container cobbler profile report --name={osconfig["profile"]}'
                            )
                            ], check=True, stdout=sbp_stdout)
            self.subproc_print(p, **opts)
            # sync it up
            self.util.print('Sync')
            subprocess.run(['sudo', 'docker', 'exec', 'cobbler_container', 'cobbler', 'sync'], check=True, stdout=sbp_stdout)

        except Exception as exc:
            self.util.print('That didn\'t work. Failing out...', quiet=opts['quiet'])
            self.util.print(exc, quiet=opts['quiet'])
            ret = False

        return ret

def main():
    ################### ARGPARSE DEFS #########################
    # args dict for use in everything
    ARGS = Util.parse_args({
        'repo_dir'      : os.environ['PWD'],
        'pconfig'       : 'provision.json',
        'override_ip'   : '',
        'tgt_os'        : None,
        'force'         : False,
        'reload'        : False,
        'quiet'         : False,
        'list_os'       : False,
        'debug'         : False
    })

    COBBLER = Cobbler(repo_dir=ARGS['repo_dir'], quiet=ARGS['quiet'])

    if ARGS['list_os']:
        OS = COBBLER.util.get_os_config()['os']
        OS_list = []
        for distro in OS:
            OS_list += COBBLER.util.get_os_config()['os'][distro]
        for _os in OS_list:
            if not _os == 'global':
                print(_os)
        exit(0)

    CFG = COBBLER.util.build_config(
        pconfig=ARGS['pconfig'],
        override_ip=ARGS['override_ip'],
        tgt_os=ARGS['tgt_os'],
        quiet=ARGS['quiet']
        )
    COBBLER.util.print(json.dumps(CFG, indent=2))
    COBBLER.util.print('=============')

    COBBLER.provision_system(CFG,
                             force=ARGS['force'],
                             reload=ARGS['reload'],
                             quiet=ARGS['quiet'],
                             debug=ARGS['debug'],
    )

    sys.stdout.flush()

if __name__ == "__main__":
    main()
