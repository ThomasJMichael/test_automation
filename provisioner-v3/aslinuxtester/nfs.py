#!/usr/bin/env python3
"""Local NFS Kernel Server controller for use by provisioner"""
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

class NFS():
    """
    Controls NFS boot setup as well as DHCP setup on the cobbler host
    If cobbler is not present, attempts to use standard DHCP filepaths

    Include by doing
    ```python
    from aslinuxtester.nfs import NFS
    from aslinuxtester.util import Util
    util = Util('/path/to/config/repo')
    nfs = NFS(util=util)
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
        Raises:
          - ValueError if neither repo_dir nor util are provided
        """

        opts = {
            'util'      : None,
            'repo_dir'  : None,
            'quiet'     : False
        }
        opts.update(kwargs)

        if opts['util']:
            self.util = opts['util']
        elif opts['repo_dir']:
            self.util = Util(repo_dir=opts['repo_dir'], quiet=opts['quiet'])
        else:
            raise ValueError("repo_dir is required if util is not provided.")

    ################### FUNCTION DEFS #########################
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
          - sigs (bool): [False] Force a signature update if installing new distros
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
            'sigs'      : False
        }
        opts.update(kwargs)

        # check if already installed
        if not opts['force']:
            try:
                self.util.connect(config, attempts=1, delay=3)
                self.util.print('Turn off the machine before running this tool.',
                                level=self.util.logging.ERROR)
                self.util.print('If you know what you\'re doing, run this command with --force.',
                                level=self.util.logging.ERROR)
                return False
            except:
                pass

        if not isinstance(config['os'], dict):
            raise TypeError(("config['os'] must be a full dictionary defining the target,"
                             "try running the name of the OS thru Util.get_os_config."))

        # define stdout for commands
        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE

        # clean profile/distro if necessary
        if opts['reload']:
            self.util.run_local(f"sudo cobbler system remove --name {config['system_name']}")
            if not self.remove_profile(config['os'], **opts):
                raise SystemError(
                    f"Could not delete cobbler profile named {config['os']['profile']}."
                    )

        # check nfs-utils installed
        if self.util.run_local('rpm -qa | grep nfs-utils', quiet=True) != 0:
            self.util.run_local('sudo yum install -y nfs-utils')

        # identify tar parms
        tar_parm = {
            "nfs" : "xvf",
            "tftp" : "xvf"
        }
        for _type in tar_parm:
            try:
                if config['os']['netboot'][_type]['tarball'].endswith('.gz'):
                    tar_parm[_type] = f"{tar_parm[_type]}z"
                if config['os']['netboot'][_type]['tarball'].endswith('.bz2'):
                    tar_parm[_type] = f"{tar_parm[_type]}j"
                if config['os']['netboot'][_type]['tarball'].endswith('.xz'):
                    tar_parm[_type] = f"{tar_parm[_type]}J"
            except:
                self.util.print(f"No tarball found for {_type}")

        # set /etc/exports
        escaped_path = config['os']['netboot']['nfs']['root'].replace('/','\/')
        self.util.run_local(f"sudo sed -i '/{escaped_path}/d' /etc/exports")
        self.util.run_local((f"echo '{config['os']['netboot']['nfs']['root']} {config['ip_address']}"
                             f"({config['os']['netboot']['nfs']['exportline']})' | "
                              "sudo tee -a /etc/exports"))
        self.util.run_local(("sudo systemctl enable nfs-server && "
                             "sudo systemctl start nfs-server && sudo exportfs -av"))

        # download nfsroot tarball and extract into place
        if not os.path.exists(config['os']['netboot']['nfs']['root']) or opts['force']:
            self.util.run_local((f"sudo rm -rf {config['os']['netboot']['nfs']['root']} && "
                                 f"sudo mkdir -p {config['os']['netboot']['nfs']['root']}"))

            if 'rsync' in config['os']['netboot']['nfs']:
                cmd = (f"cd {config['os']['netboot']['nfs']['root']} && "
                       f"sudo rsync -avxHAXrp "
                       f"{config['os']['netboot']['nfs']['rsync']} .")
                self.util.run_local(cmd)
            elif 'tarball' in config['os']['netboot']['nfs']:
                # ON SECOND THOUGHT THIS WAS DUMB, REAL MEN USE RSYNC
                self.util.run_local((f"cd {config['os']['netboot']['nfs']['root']} && "
                                     f"curl {config['os']['netboot']['nfs']['tarball']} "
                                     f"| sudo tar {tar_parm['nfs']} -"), quiet=True)
            else:
                self.util.print((f"No tarball or rsync mirror defined. Ensure you have "
                                 f"set up a proper rootfs at {config['os']['netboot']['nfs']['root']}"))

            # download kernel and initrd into place
            self.util.run_local((f"sudo rm -rf {config['os']['netboot']['tftp']['root']} && "
                                 f"sudo mkdir -p {config['os']['netboot']['tftp']['root']}"))
            self.util.run_local((f"cd {config['os']['netboot']['tftp']['root']} && "
                                 f"curl {config['os']['netboot']['tftp']['tarball']} | sudo tar {tar_parm['tftp']} -"), quiet=True)

        if not self.create_profile_if_missing(config, **opts):
            raise SystemError(
                f"Could not find or create a cobbler profile named {config['os']['profile']}."
                )

        # let cobbler do its thing
        self.util.run_local(f"sudo cobbler system remove --name {config['system_name']}")
        cmdstr = (f'sudo cobbler system add --name="{config["system_name"]}" '
                  f'--profile="{config["os"]["profile"]}-nfsboot"')
        self.util.print(f'Running {cmdstr}', quiet=opts['quiet'])
        subprocess.run(['/bin/sh', '-c', cmdstr], stdout=sbp_stdout)
        sys.stdout.flush()

        if 'ksmeta' in config:
            ks_meta = ' '.join(['{}={}'.format(ksm, config['ksmeta'][ksm]) for ksm in config['ksmeta']])
        else:
            ks_meta = ''
        if 'kopts' not in config:
            config['kopts'] = (f"console=ttyS0,115200,8,n,1 "
                               f"root=nfs:{config['gateway']}:{config['os']['netboot']['nfs']['root']} rw")
        if 'kopts_post' not in config:
            config['kopts_post'] = config['kopts']

        ksmetastring = (
                       f'dev_username={config["dev_username"]} '
                       f'dev_password={config["dev_password"]} '
                       f'{ks_meta}'
                       )
        cmdstr = (
            f'sudo cobbler system edit --name="{config["system_name"]}" '
            f'--mac="{config["mac_address"]}" --ip-address="{config["ip_address"]}" '
            f'--netmask="255.255.255.0" --static=1 --dns-name="{config["system_name"]}" '
            f'--interface="enp_cobbler" --gateway="{config["gateway"]}" '
            f'--hostname="{config["system_name"].replace("_", "-")}" '
            f'--kopts="{config["kopts"]}" '
            f'--kopts-post="{config["kopts_post"]}" '
            f'--ksmeta="{ksmetastring}" --netboot-enabled=true'
            )
        self.util.print(f'Running {cmdstr}', quiet=opts['quiet'])
        if subprocess.run([
                '/bin/sh', '-c',
                cmdstr
        ], stdout=sbp_stdout).returncode == 0:
            sys.stdout.flush()
            subprocess.run(['/bin/sh', '-c', 'sudo cobbler sync'], stdout=sbp_stdout)
            return_val = subprocess.run([
                'sudo', 'cobbler', 'system', 'report', '--name', config['system_name']
                ], stdout=sbp_stdout).returncode
        else:
            return_val = 1
        return return_val

    def remove_profile(self, osconfig, **kwargs):
        """
        Args:
          - osconfig (dict): Just the 'os' config field from util.Util.build_config
        Keyword args:
          - quiet (bool): [False] Suppress status messages
        Raises:
        Returns:
            True if successful, else False
        """
        opts = {
            'quiet' : False,
            'sigs' : False
        }
        opts.update(kwargs)

        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE
        proc = subprocess.run([
            '/bin/sh', '-c', f'sudo cobbler profile report --name {osconfig["profile"]}-nfsboot'
        ], stdout=subprocess.DEVNULL)

        if proc.returncode != 0:
            self.util.print(f'Profile {osconfig["profile"]}-nfsboot does not exist.')
            return True

        cmd = f'sudo cobbler profile remove --name {osconfig["profile"]}-nfsboot'
        proc = subprocess.run(['/bin/sh', '-c', cmd], stdout=sbp_stdout)
        if proc.returncode != 0:
            self.util.print(f'Failed to run {cmd}')
            return False

        cmd = f'sudo cobbler distro remove --name {osconfig["distro"]}-nfsboot'
        proc = subprocess.run(['/bin/sh', '-c', cmd], stdout=sbp_stdout)
        if proc.returncode != 0:
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
          - sigs (bool): [False] Skip cobbler signature update
        Raises:
          - IOError if supplied with an invalid filepath for an ISO to import
        Returns:
            True if successful, else False
        """
        opts = {
            'quiet' : False,
            'sigs' : False
        }
        opts.update(kwargs)
        osconfig = tgt_cfg['os']
        sbp_stdout = subprocess.DEVNULL if opts['quiet'] else subprocess.PIPE

        # check existing profiles for a match
        proc = subprocess.run([
            '/bin/sh', '-c', f'sudo cobbler profile report --name {osconfig["profile"]}-nfsboot'
        ], stdout=subprocess.DEVNULL)

        if proc.returncode == 0:
            return True

        # its go time
        ret = True
        self.util.print('Doing a cobbler sync for sanity')
        subprocess.run([
            '/bin/sh', '-c', f'sudo cobbler sync'
        ], stdout=subprocess.DEVNULL)
        subprocess.run([
            '/bin/sh', '-c', f'sudo systemctl restart cobblerd'
        ], stdout=subprocess.DEVNULL)
        time.sleep(2)

        try:

            # detect distro, if not found import fresh
            self.util.print(f'Looking for existing distro {osconfig["profile"]}-nfsboot-x86_64')
            proc = subprocess.run([
                '/bin/sh', '-c', f'sudo cobbler distro report --name {osconfig["profile"]}-nfsboot-x86_64'
            ], stdout=subprocess.DEVNULL)

            if proc.returncode != 0:
                # spawn a proper distro to use
                self.util.print('Creating NFS Bootable cobbler distro')
                subprocess.run(['/bin/sh', '-c',
                                (
                                    f'sudo cobbler distro add --name={osconfig["distro"]}-nfsboot '
                                    f'--kernel={osconfig["netboot"]["tftp"]["root"]}/'
                                    f'{osconfig["netboot"]["tftp"]["kernel"]} '
                                    f'--initrd={osconfig["netboot"]["tftp"]["root"]}/'
                                    f'{osconfig["netboot"]["tftp"]["initrd"]} --arch=x86_64 '
                                )
                                ], check=True, stdout=sbp_stdout)
                # delete and recreate the profile
                self.util.print('Removing new profile')
                #subprocess.run(['/bin/sh', '-c',
                #                f'sudo cobbler profile remove --name={osconfig["distro"]}-nfsboot-x86_64'
                #                ], check=True, stdout=sbp_stdout)
            else:
                self.util.print('Distro found in cobbler')

            self.util.print('Creating new profile')
            subprocess.run(['/bin/sh', '-c',
                            (
                                f'sudo cobbler profile add --name={osconfig["profile"]}-nfsboot '
                                f'--distro={osconfig["distro"]}-nfsboot --kickstart=""'
                            )
                            ], check=True, stdout=sbp_stdout)
            # sync it up
            self.util.print('Restarting cobblerd')
            subprocess.run(['sudo', 'cobbler', 'sync'], check=True, stdout=sbp_stdout)
            subprocess.run([
                'sudo', 'service', 'cobblerd', 'restart'
                ], check=True, stdout=sbp_stdout)
            time.sleep(2)

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
        'mac'           : '',
        'tgt_os'        : None,
        'force'         : False,
        'reload'        : False,
        'quiet'         : False,
        'sigs'          : False,
        'list_os'       : False,
        'no_wait'       : False
    })

    _NFS = NFS(repo_dir=ARGS['repo_dir'], quiet=ARGS['quiet'])

    if ARGS['list_os']:
        OS = _NFS.util.get_os_config()['os']
        OS_list = []
        for distro in OS:
            OS_list += _NFS.util.get_os_config()['os'][distro]
        for _os in OS_list:
            if not _os == 'global':
                print(_os)
        exit(0)

    CFG = _NFS.util.build_config(
        pconfig=ARGS['pconfig'],
        override_ip=ARGS['override_ip'],
        mac=ARGS['mac'],
        tgt_os=ARGS['tgt_os'],
        quiet=ARGS['quiet']
        )
    print(json.dumps(CFG, indent=2))
    print('=============')
    sys.stdout.flush()

    _NFS.provision_system(CFG,
                         force=ARGS['force'],
                         reload=ARGS['reload'],
                         quiet=ARGS['quiet'],
                         sigs=ARGS['sigs'],
    )
    exit()
    _NFS.util.reboot(CFG, no_wait=ARGS['no_wait'], connectargs={
                    'attempts' : 100,
                    'delay'    : 10,
                    'quiet'    : ARGS['quiet']
                    })

if __name__ == "__main__":
    main()
