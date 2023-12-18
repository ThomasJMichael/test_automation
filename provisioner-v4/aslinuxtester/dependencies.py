#!/usr/bin/env python3
"""The dependency manager of the provisioning system"""
import sys
import os
import json
from string import ascii_letters
from random import choice
try:
    from .util import Util
except ImportError:
    from util import Util
try:
    from .validator import Validator
except ImportError:
    from validator import Validator

class Dependencies():
    """
    Controls the configuration of the machine as defined in a config file in 6 steps:

    1. Install Repository files (if configured)
    2. Install SSH Keyfiles (if configured)
    3. Run prereq scripts (if configured)
    4. Install all configured packages
    5. Run postreq scripts (if configured)
    6. Run driver install scripts

    When this is finished, Util.set_target_config is called to mark the target system
    as provisioned.

    Alternatively, each step can be called individually, allowing the user to control
    the provisioning process in its entirety.

    Include by doing
    ```python
    from aslinuxtester.dependencies import Dependencies
    from aslinuxtester.util import Util
    util = Util('/path/to/config/repo')
    dpnd = Dependencies(util=util)
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
            ValueError if neither repo_dir nor util are provided
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

        self.validator = Validator(util=self.util)

    ################### FUNCTION DEFS #########################
    def install_all(self, tgt_cfg, **kwargs):
        """
        Installs all dependencies defined in the pconfig, in the order described in
        the module docstring above.

        Args:
          - tgt_cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - force (bool): [False] Skip target config checking and start the installations
          - quiet (bool): [False] Set to true to hide status messages
          - attempts (int): [100] How many times to retry connection
          - delay (int): [10] How long to wait between retries
        """
        opts = {
            'force'     : False,
            'quiet'     : False,
            'attempts'  : 100,
            'delay'     : 10
        }
        opts.update(kwargs)

        # SSH into UUT and install package dependencies
        self.util.connect(tgt_cfg, **{
                          'attempts' : opts['attempts'],
                          'delay'    : opts['delay'],
                          'quiet'    : opts['quiet']
                          })

        #if self.util.iboot:
        #    self.util.reboot(tgt_cfg)

        # check if already installed
        if not opts['force'] and self.util.check_target_config(tgt_cfg, quiet=opts['quiet']):
            return
        else:
            self.util.print("Forcing provisioning on target...")

        # start installing stuff
        self.install_repos(tgt_cfg)
        self.install_keyfiles(tgt_cfg)
        if 'ansible_file' in tgt_cfg:
            self.install_ansible(tgt_cfg)
        else:
            self.install_prereqs(tgt_cfg)
            self.install_packages(tgt_cfg)
            self.install_postreqs(tgt_cfg)
            self.install_drivers(tgt_cfg)

        # Reconnect in case of reboot in scripts
        self.util.connect(tgt_cfg, **{
                          'attempts' : opts['attempts'],
                          'delay'    : opts['delay'],
                          'quiet'    : opts['quiet']
                          })

        # mark as completely installed
        self.util.set_target_config(tgt_cfg, quiet=opts['quiet'])

    def install_repos(self, cfg, **kwargs):
        """
        Installs all global and OS-specific repos described in os.json to /etc/yum.repos.d

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - extrarepos (list): [[]] A list of repo definitions following the format of os.json
          - clear_existing (bool): [False] Attempt to backup existing yum repo files to
            $HOME/yumrepo.bak
          - quiet (bool): [False] Set to true to hide status messages
        Returns:
            The number of repos installed
        Raises:
          - paramiko.ssh_exception.SSHException if a repo fails to install
        """
        opts = {
            'extrarepos'        : [],
            'clear_existing'    : False,
            'quiet'             : False
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        self.util.print("Attempting to install configured repos...")

        ret = 0
        repos = opts['extrarepos']
        if 'repos' in cfg['os'] and isinstance(cfg['os']['repos'], list):
            repos.extend(cfg['os']['repos'])

        for repo in repos:
            self.util.print(f'Installing {repo["name"]}.repo...', quiet=opts['quiet'])
            self.util.run_command((f'echo "[{repo["name"]}]" > '
                                   f'{repo["name"]}.repo'), quiet=True)
            self.util.run_command((f'echo "name={repo["name"]}" >> '
                                   f'{repo["name"]}.repo'), quiet=True)
            self.util.run_command((f'echo "baseurl={repo["baseurl"]}" >> '
                                   f'{repo["name"]}.repo'), quiet=True)
            self.util.run_command((f'echo "enabled=1" >> '
                                   f'{repo["name"]}.repo'), quiet=True)
            if 'extraoptions' in repo and isinstance(repo['extraoptions'], dict):
                for opt in repo['extraoptions']:
                    self.util.run_command((f'sed -i "/{opt}=/d" '
                                           f'{repo["name"]}.repo'), quiet=True)
                    self.util.run_command((f'echo "{opt}={repo["extraoptions"][opt]}" >> '
                                           f'{repo["name"]}.repo'), quiet=True)

            # move it on up
            if self.util.run_command((f'sudo -E mv {repo["name"]}.repo '
                                      f'/etc/yum.repos.d/{repo["name"]}.repo')) == 0:
                ret += 1
            else:
                self.util.print(f'Installation of {repo["name"]}.repo failed!', quiet=opts['quiet'])
        return ret

    # these are necessary to pull files passwordless from git
    # sshconfig key will need to be configured in someones gitlab account
    def install_keyfiles(self, cfg, **kwargs):
        """
        Copies SSH Configuration files to the target. This usually entails an
        id_rsa file, its associated public key, and a config file to define its
        usage. Should virtually always be copied to $HOME/.ssh, but the
        location is configurable via Util.remote_filepaths['sshconfig'].

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
        Returns:
            The number of files copied
        """
        opts = {
            'quiet' : False
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        ret = 0
        if not self.util.local_filepaths['sshconfig']:
            self.util.print('SSH Config directory is unset', quiet=opts['quiet'])
        elif not os.path.isdir(self.util.local_filepaths['sshconfig']):
            self.util.print(f"No ssh config directory at {self.util.local_filepaths['sshconfig']}.",
                            quiet=opts['quiet'])
        else:
            self.util.print("Attempting to install ssh keyfiles...", quiet=opts['quiet'])
            #if not opts['ftp_client']:
            #    opts['ftp_client'] = self.util._client.open_sftp()
            #    ftpflag = True
            #rem_ssh_folder = f'{self.util.remote_filepaths["sshconfig"]}'

            #if not os.path.dirname(rem_ssh_folder) in opts['ftp_client'].listdir(os.path.basename(rem_ssh_folder):
            #opts['ftp_client'].mkdir(rem_ssh_folder)
            for sshconf in os.listdir(self.util.local_filepaths['sshconfig']):
                lfile = f'{self.util.local_filepaths["sshconfig"]}/{sshconf}'
                rfile = f'{self.util.remote_filepaths["sshconfig"]}/{sshconf}'
                ret += self.util.copy_file(
                    lfile,
                    rfile,
                    perm=0o600,
                    quiet=opts['quiet'])
            self.util.run_command('chmod 700 ~/.ssh', quiet=True, strict=True)

        return ret

    def install_ansible(self, cfg, **kwargs):
        """
        Install ansible on the target (or at least attempts to). Copies all files
        in Util.local_filepaths['ansiblefiles'] to the target, then attempts to run them

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - quiet (bool): [False] Set to true to hide status messages
        Returns:
            The exit code of ansible
        Raises:
        """
        opts = {
            'quiet'             : False
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        rnd = ''.join(choice(ascii_letters) for x in range(5))
        pconfig = f'/tmp/pconfig-{rnd}.json'
        with open(pconfig, 'w') as pconfigfile:
            json.dump(cfg, pconfigfile, indent=2)
        print(pconfig)
        self.util.run_command((f'ansible-playbook -i {cfg["ip_address"]}, '
                               f'{self.util.local_filepaths["repo_dir"]}/'
                               f'{cfg["ansible_file"]} '
                               f'--extra-vars pconfig={pconfig}'),
                              local=True, strict=True)
        self.util.run_local(f'rm -rf {pconfig}')

    def install_prereqs(self, cfg, **kwargs):
        """
        Copies all files in Util.local_filepaths['prereqscripts'] to the target, then
        attempts to run them in alphanumeric order. If the path is unset or the
        directory is missing, fails out gracefully.

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - ignore_scripts (list): [[]] List of script names to ignore
          - quiet (bool): [False] Set to true to hide status messages
          - strict (bool): [True] Throw an error if a prereq script fails
        Returns:
            The number of scripts run
        Raises:
          - paramiko.ssh_exception.SSHException if strict=True and a command fails
        """
        ret = 0
        opts = {
            'ignore_scripts'    : [],
            'quiet'             : False,
            'strict'            : True
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        if not self.util.local_filepaths['prereqscripts']:
            self.util.print("Prereq script directory is unset.", quiet=opts['quiet'])
        elif not os.path.isdir(self.util.local_filepaths['prereqscripts']):
            self.util.print(f"No prereq dir at {self.util.local_filepaths['prereqscripts']}.",
                            quiet=opts['quiet'])
        else:
            self.util.print("Attempting to install prereq scripts...", quiet=opts['quiet'])

            # do the copy
            scriptlist = sorted(os.listdir(self.util.local_filepaths['prereqscripts']))
            if 'prereqs' in cfg:
                self.util.print(f'Prereqs list set to {cfg["prereqs"]} from config file',
                                quiet=opts['quiet'])
                scriptlist = cfg['prereqs']
            for scr in scriptlist:
                if scr in opts['ignore_scripts']:
                    self.util.print(f'Skipping {scr}', quiet=opts['quiet'])
                    continue
                lscript = f'{self.util.local_filepaths["prereqscripts"]}/{scr}'
                rscript = f'{self.util.remote_filepaths["prereqscripts"]}/{scr}'
                self.util.copy_file(
                    lscript,
                    rscript,
                    perm=0o711,
                    quiet=opts['quiet']
                    )

                # run script
                if self.util.run_command(
                        rscript,
                        strict=opts['strict'],
                        quiet=opts['quiet']
                    ) == 0:
                    ret += 1
                else:
                    self.util.print(f'{scr} failed', quiet=opts['quiet'])
        return ret

    def _detect_package_manager(self, cfg):
        """
        Detects the package manager used by the currently connected util library
        and returns the string containing the command. Otherwise raises a ValueError
        because I couldn't think of a better one to spit out
        """

        ### ADD SUDO TO LINUX PACKAGE MANAGERS TO REMOVE WINDOWS BUG
        pkgman = None
        self.util.connect(cfg)

        # check for choco. This is a required prereq for windows installs
        if self.util.run_command('choco -v', quiet=True) == 0:
            pkgman = 'choco'
        # check for zypper
        elif self.util.run_command('[ -n "$(which zypper 2>/dev/null)" ]', quiet=True) == 0:
            pkgman = 'zypper'
        # check for apt
        elif self.util.run_command('[ -n "$(which apt-get 2>/dev/null)" ]', quiet=True) == 0:
            pkgman = 'apt-get'
        # check for dnf
        elif self.util.run_command('[ -n "$(which dnf 2>/dev/null)" ]', quiet=True) == 0:
            pkgman = 'dnf'
        # check for yum
        elif self.util.run_command('[ -n "$(which yum 2>/dev/null)" ]', quiet=True) == 0:
            pkgman = 'yum'
        else:
            raise ValueError('I don\'t know how to install packages on this system.')

        return pkgman

    def install_packages(self, cfg, **kwargs):
        """
        Uses the detected package manager to install packages as listed in OS config

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - extrapackges (list): [[]] List of extra packages to install
          - pkgmanager (str): ['yum'] Package manager to use
          - quiet (bool): [False] Set to true to hide status messages
          - strict (bool): [True] Throw an error if a prereq script fails
        Returns:
            The number of packages installed
        Raises:
          - paramiko.ssh_exception.SSHException if strict=True and a command fails
        """
        opts = {
            'extrapackages' : [],
            'pkgmanager'    : self._detect_package_manager(cfg),
            'quiet'         : False,
            'strict'        : True
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        self.util.print("Attempting to install packages...", quiet=opts['quiet'])

        # build package list
        pkglist = opts['extrapackages']
        if 'packages' in cfg['os'] and cfg['os']['packages']:
            pkglist.extend(cfg['os']['packages'])

        # install packages
        if pkglist:
            self.util.print(f'Installing {len(pkglist)} packages...', quiet=opts['quiet'])
            routefix = f'sudo -E pkill {opts["pkgmanager"]} || : '
            cmdstr = f'{routefix} && sudo -E {opts["pkgmanager"]} install -y {" ".join(pkglist)}'
            if self.util.run_command(
                    cmdstr,
                    strict=opts['strict'],
                    quiet=opts['quiet']
                ) != 0:
                pkglist = []
        else:
            self.util.print('No packages listed for installation.', quiet=opts['quiet'])
        return len(pkglist)

    def install_postreqs(self, cfg, **kwargs):
        """
        Copies all files in Util.local_filepaths['postreqscripts'] to the target, then
        attempts to run them in alphanumeric order. If the path is unset or the
        directory is missing, fails out gracefully.

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - ignore_scripts (list): [[]] List of script names to ignore
          - quiet (bool): [False] Set to true to hide status messages
          - strict (bool): [True] Throw an error if a postreq script fails
        Returns:
            The number of scripts run
        Raises:
          - paramiko.ssh_exception.SSHException if strict=True and a command fails
        """
        ret = 0
        opts = {
            'ignore_scripts'    : [],
            'quiet'             : False,
            'strict'            : True
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        ret = 0
        if not self.util.local_filepaths['postreqscripts']:
            self.util.print("Postreq script directory is unset.", quiet=opts['quiet'])
        elif not os.path.isdir(self.util.local_filepaths['postreqscripts']):
            self.util.print(f"No postreq dir at {self.util.local_filepaths['postreqscripts']}.",
                            quiet=opts['quiet'])
        else:
            self.util.print("Attempting to install postreq scripts...", quiet=opts['quiet'])
            # do the copy
            scriptlist = sorted(os.listdir(self.util.local_filepaths['postreqscripts']))
            if 'postreqs' in cfg:
                self.util.print(f'Prereqs list set to {cfg["postreqs"]} from config file',
                                quiet=opts['quiet'])
                scriptlist = cfg['postreqs']
            for scr in scriptlist:
                if scr in opts['ignore_scripts']:
                    self.util.print(f'Skipping {scr}', quiet=opts['quiet'])
                    continue
                lscript = f'{self.util.local_filepaths["postreqscripts"]}/{scr}'
                rscript = f'{self.util.remote_filepaths["postreqscripts"]}/{scr}'
                self.util.copy_file(
                    lscript,
                    rscript,
                    perm=0o711,
                    quiet=opts['quiet']
                    )

                # run script
                if self.util.run_command(
                        rscript,
                        strict=opts['strict'],
                        quiet=opts['quiet']
                    ) == 0:
                    ret += 1
                else:
                    self.util.print(f'{scr} failed', quiet=opts['quiet'])
        return ret

    def install_drivers(self, cfg, **kwargs):
        """
        Copies all files in Util.local_filepaths['postreqscripts'] to the target, then
        attempts to run them in alphanumeric order. If the path is unset or the
        directory is missing, fails out gracefully.

        Args:
          - cfg (dict): The configuration of the target from Util.build_config
        Keyword args:
          - ignore_drivers (list): [[]] List of driver install script names to ignore
          - quiet (bool): [False] Set to true to hide status messages
          - strict (bool): [True] Throw an error if a postreq script fails
        Returns:
            The number of driver install scripts run successfully
        Raises:
          - paramiko.ssh_exception.SSHException if strict=True and a command fails
        """
        ret = 0
        opts = {
            'ignore_drivers'    : [],
            'quiet'             : False,
            'strict'            : True
        }
        opts.update(kwargs)
        self.util.connect(cfg)

        ret = 0
        if not self.util.local_filepaths['driverscripts']:
            self.util.print("Driver script directory is unset.", quiet=opts['quiet'])
        elif not os.path.isdir(self.util.local_filepaths['driverscripts']):
            self.util.print(f"No driver dir at {self.util.local_filepaths['driverscripts']}.",
                            quiet=opts['quiet'])
        else:
            self.util.print("Attempting to install drivers...", quiet=opts['quiet'])
            for scr in sorted(cfg['drivers']):
                if not scr in os.listdir(self.util.local_filepaths['driverscripts']):
                    self.util.print((f" Could not find install script at "
                                     f"{self.util.local_filepaths['driverscripts']}/{scr}"),
                                    quiet=opts['quiet'])
                    if opts['strict']:
                        raise IOError
                    else:
                        continue
                lscript = f'{self.util.local_filepaths["driverscripts"]}/{scr}'
                rscript = f'{self.util.remote_filepaths["driverscripts"]}/{scr}'
                self.util.copy_file(
                    lscript,
                    rscript,
                    perm=0o711,
                    )
                if not os.path.isdir(self.util.local_filepaths["logs"]):
                    os.makedirs(self.util.local_filepaths["logs"])
                with open((f'{self.util.local_filepaths["logs"]}/'
                           f'{cfg["os"]["profile"]}-{scr}.install.log'), 'w') as installf:
                    if self.util.run_command(
                            f'{rscript} 2>&1',
                            strict=opts['strict'],
                            quiet=opts['quiet'],
                            file=installf
                        ) == 0:
                        ret += 1

def main():
    ARGS = Util.parse_args({
        'repo_dir'      : os.environ['PWD'],
        'pconfig'       : 'provision.json',
        'override_ip'   : '',
        'tgt_os'        : None,
        'force'         : False,
        'quiet'         : False,
        'repos'         : False,
        'prereqs'       : False,
        'packages'      : False,
        'postreqs'      : False,
        'keyfiles'      : False,
        'drivers'       : False,
    })
    INDIV_RUNNERS = ( ARGS['repos'] or
                      ARGS['prereqs'] or
                      ARGS['packages'] or
                      ARGS['postreqs'] or
                      ARGS['keyfiles'] or
                      ARGS['drivers'])
    DPND = Dependencies(repo_dir=ARGS['repo_dir'])
    CFG = DPND.util.build_config(
        pconfig=ARGS['pconfig'],
        override_ip=ARGS['override_ip'],
        tgt_os=ARGS['tgt_os']
    )
    print(json.dumps(CFG, indent=2))
    print('=============')
    sys.stdout.flush()

    if ARGS['repos']:
        DPND.install_repos(CFG, **ARGS)
    if ARGS['prereqs']:
        DPND.install_prereqs(CFG, **ARGS)
    if ARGS['packages']:
        DPND.install_packages(CFG, **ARGS)
    if ARGS['postreqs']:
        DPND.install_postreqs(CFG, **ARGS)
    if ARGS['keyfiles']:
        DPND.install_keyfiles(CFG, **ARGS)
    if ARGS['drivers']:
        DPND.install_drivers(CFG, **ARGS)
    if not INDIV_RUNNERS:
        DPND.install_all(CFG, **ARGS)

if __name__ == "__main__":
    main()
