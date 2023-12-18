# Class aslinuxtester.validator.Validator  
- [Source for this class](../../aslinuxtester/validator.py)
- [Full Library Documentation](../../README.md)  
- [Example Usage](examples.md)  

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

### **__init__**(self, **kwargs)  [[source](../../aslinuxtester/validator.py#L31)]  
    If util is supplied at init, set the class-level util to that object.  
    Otherwise, requires a repo_dir to initialize a new util.Util  
      
    Keyword args:  
      - util (util.Util): [None] A previously initialized util.Util object  
      - repo_dir (str): [None] The path to the configuration repository  
    Raises:  
      - ValueError if neither repo_dir nor util are provided  

### **provisioner_config**(self, pconfig, **kwargs)  [[source](../../aslinuxtester/validator.py#L56)]  
    Validates all optional and required fields for a specified Provisioner Config  
    file in repo_dir  
      
    Args:  
      - pconfig (str|dict): The provisioner config file to validate  
    Keyword args:  
      - quiet (bool): [False] Set to true to hide status messages  
      - verbose (bool): [False] Print INFO messages  
    Returns:  
      #TODO  

### **os_config**(self, oconfig, **kwargs)  [[source](../../aslinuxtester/validator.py#L225)]  
    Validates all optional and required fields for a specified OS Config  
    file in repo_dir  
      
    Args:  
      - oconfig (str): The provisioner config file to validate  
    Keyword args:  
      - quiet (bool): [False] Set to true to hide status messages  
      - verbose (bool): [False] Print INFO messages  
    Returns:  
      #TODO  

