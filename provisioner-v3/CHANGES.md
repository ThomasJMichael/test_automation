##### 5.3.8 [Denver Atwood]
- better oopsie-proofing in testTool test pull function

##### 5.3.7 [John Ellis]
- adding make, make install to deps.sh

##### 5.3.6 [Denver Atwood]
- fixed nfs.py to behave correctly when not run with --force

##### 5.3.5 [Denver Atwood]
- deps.sh updated to skip pyhton install if correct version detected

##### 5.3.4 [Trenton Williams]
- Fixed issue with host logs not being saved off to main log folder

##### 5.3.3 [Denver Atwood]
- encase ansible-playbook paths in quotes to avoid pesky spaces

##### 5.3.2 [Denver Atwood]
- changed NFS to not rebuild root unless told to or missing

##### 5.3.1 [Denver Atwood]
- adding MAC address param to util library to enable dynamic runs
- added permissions preservation to nfs tool

##### 5.3.0 [Denver Atwood]
- Adding NFSTool 
- changed up some util.py operations

##### 5.2.6 [Denver Atwood]
- Recreate connection to fix SFTP shenanigan

##### 5.2.5 [Denver Atwood]
- Fixing strict setting on ansible runs to fail properly
- Making testTool fail gracefully on no logs found

##### 5.2.4 [Denver Atwood]
- Fixed testTool return values always going positive
- Fixed util bug where undefined OS leads to typeError

##### 5.2.3 [Denver Atwood]
- Cleaned up mechanism for extending pconfig using osconfig

##### 5.2.2 [Denver Atwood]
- Added kopts to cobbler system initialization
- added nfsroot potential stubs
- added ansible support in osconfig files
- lots of QOL fixes in util

##### 5.2.1 [Denver Atwood]
- Remove telnet shenanigans for iboot, as they are terrible.

##### 5.2.0 [Denver Atwood]
- Set up initial ansible pull support 

##### 5.1.1 [Denver Atwood]
- Made no-wait reboot but not wait for a reconnect

##### 5.1.0 [Denver Atwood]
- Added outlet support for iBoot power bars
- changed all iBoot support to use telnet instead of Web API
- Added no-wait option to cobblerTool 

##### 5.0.7 [Trenton Williams]
- File copy fixes

##### 5.0.6 [Denver Atwood]
- Fixed forced reboot

##### 5.0.5 [Trenton Williams]
- Added forced reboot, migrated to new repo

##### 5.0.4 [Trenton Williams]
- fixed issue with --list_os argument not reading new os.json layout correctly

##### 5.0.4 [Trenton Williams]
- fixed missing newline from driver installation logs

##### 5.0.3 [Trenton Williams]
- fixed distro naming error that occurred within build_config

##### 5.0.2 [Denver Atwood]
- force /etc/profile to run on every command

##### 5.0.1 [Denver Atwood, Trenton Williams]
- added list_os flag to cobblerTool
- added quiet option to Util init
- added local_filepaths and remote_filepaths as config options

##### 5.0.0 [Denver Atwood, Trenton Williams]
- added local command functionality to util library
- reran documentation builder becuase i oopsied last time
- added type print to all help texts
- added atrocious kickstart file/cobbler profile naming conventions
- added multi profile/distro code
- unfucked the iboot controller
- implemented reboot via iboot as default choice for all operations

##### 4.1.0 [Denver Atwood]
- added current_ip directive for all commands

##### 4.0.17 [Denver Atwood]
- added remove_profile to forced cobbler install
- added option to force reinstall of OS

##### 4.0.16 [Denver Atwood]
- added cobblerd restart and sigs option to cobbler.py

##### 4.0.15 [Denver Atwood]
- fixed sudo commands to preserve proxy

##### 4.0.14 [Denver Atwood]
- added delay to fix cobbler failing to be up on rerun after adding profile

##### 4.0.13 [Denver Atwood]
- added signature update to create profile flow

##### 4.0.12 [Denver Atwood]
- added install drivers option to deps since i apparently forgot to do that one...

##### 4.0.11 [Denver Atwood]
- added a bunch of options to dependencies runner to enable deep debug

##### 4.0.10 [Denver Atwood]
- update validator and i guess some util changes? idk actually but the repo was dirty

##### 4.0.9 [Denver Atwood]
- Fixing error for invalid OS
- fixing docs for fetch_logs
- fixing copy path creation in get_file

##### 4.0.7 [Denver Atwood]
- adding compression option to fetch logs
- fixing some shenanigans in test.py

##### 4.0.6 [Denver Atwood]
- fixed fetch_logs path

##### 4.0.5 [Denver Atwood]
- fixed return value for fetch_logs

##### 4.0.3 [Denver Atwood]
- fixing os config loading and erroring

##### 4.0.3 [Denver Atwood]
- fixed AutoAddPolicy syntax

##### 4.0.2 [Denver Atwood]
- fixed version stamp in changelog for 4.0.1
- that variable didnt exist yet woops

##### 4.0.1 [Denver Atwood]
- fixed fetch_logs 'path' behavior to make sense 

##### 4.0.0 [Denver Atwood]
- added windows connect target support
- added windows powershell and command support
- added windows chocolatey support
- added requirement for OS type defs in oconfig json file
- fixed several functions to consume correct params for OS typing

##### 3.2.1 [Denver Atwood]
- added 'extra_lists' support to osconfig file 
- added an update_dicts function to standardize behavior

##### 3.2.0 [Denver Atwood]
- fixed .ssh folder permissions enabling passwordless ssh
- added file and dictionary validator
- added doc for some other things
- added console scripts to the setuptools description

##### 3.1.2 [Denver Atwood]
- Adding iBoot config field and controls 
- doc for iboot class
- Added requests to Pipfile
- svn support for test repos
- Cleaner parseargs definitions
- Added package manager support (no yum default anymore)
- Added variable retry time and attempts for deps fns
- fixed return values for cobbler functions
- fixing naming conventions for iboot

##### 3.1.1 [Denver Atwood]
- Added logger to Util class
- Perfected the log format
- Added really useful name formatting for Print
- level based logging

##### 3.1.0 [Denver Atwood]
- Added returns to provision_system call
- Added line number linking to doc
- Added more verbosity to cobbler for QOL
- Fixing more doc
- Updating parseargs for direct running
- Unified print function.... very strong
- Changed init method for Util

##### 3.0.2 [Denver Atwood]
- Fixed the missing host key bug permanently

##### 3.0.1 [Denver Atwood]
- Fixed some formatting
- Added TypeError on bad OS Config
- More host key ignoring

##### 3.0.0 [Denver Atwood]
- Added several example files and documented all API endpoints
- Changed call structure for most test functions
- Cleaned up dependency resolution a LOT
- Added better error handling/throwing for several functions

##### 2.0.4 [Denver Atwood]
- Added interactive shell to run_command
- Added tons of documentation
- Doc can now be generated by calling `python3 setup.py doc`

##### 2.0.3 [Denver Atwood]
- Call me the friggin doc man

##### 2.0.2 [Denver Atwood]
- Added util tests
- Updated docstrings to google format

##### 2.0.1 [Denver Atwood]
- Fixing Util initializer everywhere
- Added docstrings to all of util.Util
- added doc.py to generate docs because why not
- added a requirements.txt and referenced it in setup.py
- Updated Pipfile

##### 2.0.0 [Denver Atwood]
- I sorted the wrong list
- Those needed to be f-strings a while ago
- Added repo installer
- Removed dependency on repo_dir for most member functions
- Added cobbler import support for new/unrecognized distros
- Added custom repo addition

##### 1.0.8 [Denver Atwood]
- Sorted test list to enforce order alphabetically

##### 1.0.7 [Denver Atwood]
- Added return codes to test runner

##### 1.0.6 [Denver Atwood]
- Fixed test pull to use branches

##### 1.0.5 [Denver Atwood]
- Added repo_dir reqt to Util init
- Discovered an interesting formatting bug in a test

##### 1.0.4 [Denver Atwood]
- Removed some useless debug text
- Fixed completely broken cobbler config port 
- That string definitely should have been formatted

##### 1.0.3 [Denver Atwood]
- Fixed pathing for provisionfile
- Fixed pconfig naming convention issue

##### 1.0.2 [Denver Atwood]
- Removed dependency on external cobbler control scripts
