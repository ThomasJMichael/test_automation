# Class aslinuxtester.dependencies.Dependencies  
- [Source for this class](../../aslinuxtester/dependencies.py)
- [Full Library Documentation](../../README.md)  
- [Example Usage](examples.md)  

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

### **__init__**(self, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L43)]  
    If util is supplied at init, set the class-level util to that object.  
    Otherwise, requires a repo_dir to initialize a new util.Util  
      
    Keyword args:  
      - util (util.Util): [None] A previously initialized util.Util object  
      - repo_dir (str): [None] The path to the configuration repository  
    Raises:  
        ValueError if neither repo_dir nor util are provided  

### **install_all**(self, tgt_cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L70)]  
    Installs all dependencies defined in the pconfig, in the order described in  
    the module docstring above.  
      
    Args:  
      - tgt_cfg (dict): The configuration of the target from Util.build_config  
    Keyword args:  
      - force (bool): [False] Skip target config checking and start the installations  
      - quiet (bool): [False] Set to true to hide status messages  
      - attempts (int): [100] How many times to retry connection  
      - delay (int): [10] How long to wait between retries  

### **install_repos**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L122)]  
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

### **install_keyfiles**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L180)]  
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

### **install_ansible**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L227)]  
    Install ansible on the target (or at least attempts to). Copies all files  
    in Util.local_filepaths['ansiblefiles'] to the target, then attempts to run them  
      
    Args:  
      - cfg (dict): The configuration of the target from Util.build_config  
    Keyword args:  
      - quiet (bool): [False] Set to true to hide status messages  
    Returns:  
        The exit code of ansible  
    Raises:  

### **install_prereqs**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L258)]  
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

### **_detect_package_manager**(self, cfg)  [[source](../../aslinuxtester/dependencies.py#L322)]  
    Detects the package manager used by the currently connected util library  
    and returns the string containing the command. Otherwise raises a ValueError  
    because I couldn't think of a better one to spit out  

### **install_packages**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L353)]  
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

### **install_postreqs**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L400)]  
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

### **install_drivers**(self, cfg, **kwargs)  [[source](../../aslinuxtester/dependencies.py#L464)]  
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

