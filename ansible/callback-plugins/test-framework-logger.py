import os
from ansible.plugins.callback import CallbackBase
import json

class CallbackModule(CallbackBase):
    """
    Callback plugin that logs test results and log ansible failures.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'test_logger'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.log_path = None
        self.log_filename = None
        self.board_name = None
        self.log_data = {
            'ansible_failures': [],
            'test_results': []
        }

    def v2_runner_on_start(self, host, task):
        self._display.display(f"Starting task: {task.get_name()}")  

        super(CallbackModule, self).v2_runner_on_start(host, task)  

    def v2_playbook_on_play_start(self, play):
        """
        Called at the start of each play.
        """
        super(CallbackModule, self).v2_playbook_on_play_start(play)
        self._display.display(f"PLAY [{play.name}] *********************************************************************")

        # Attempt to set log_path and log_filename only if they are None
        if self.log_path is None or self.log_filename is None:
            localhost_vars = play.get_variable_manager().get_vars(play=play).get('hostvars', {}).get('localhost', {})
            if self.log_path is None:
                self.log_path = localhost_vars.get('log_path')

            if self.log_filename is None:
                self.log_filename = localhost_vars.get('log_filename')

            # Now check if the variables have been set
            if self.log_path is not None and self.log_filename is not None:
                print(f"log path: {self.log_path}")
                print(f"log filename: {self.log_filename}")

    def v2_runner_on_ok(self, result):
        self._display.display(f"Task passed: {result._task.get_name()}")
        if 'test_summary' in result._task.tags:
            # Extract the test role name from the task's file path
            task_file_path = result._task.get_path()
            if task_file_path:
                # Split the path and find the index of 'tests' to extract the test name
                path_parts = task_file_path.split(os.sep)
                if 'tests' in path_parts:
                    test_index = path_parts.index('tests') + 1
                    test_name = path_parts[test_index] if len(path_parts) > test_index else "unknown"
                else:
                    test_name = "unknown"
            else:
                test_name = "unknown"
            
            host = result._host.get_name()
            hostvars = result._task._variable_manager.get_vars()
            current_os = hostvars['hostvars'][host].get('ansible_distribution', 'unknown')
            current_os_version = hostvars['hostvars'][host].get('ansible_distribution_version', 'unknown')
            
            test_status = "passed"  
            
            self.log_data['test_results'].append({
                'test_name': test_name,
                'current_os': f"{current_os} {current_os_version}",
                'status': test_status
            })

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """
        Logs ansible task failures and test failures.
        Ignores errors which are ignored while running
        """
        host = result._host.get_name()
        hostvars = result._task._variable_manager.get_vars()
        current_os = hostvars['hostvars'][host].get('ansible_distribution', 'unknown')
        current_os_version = hostvars['hostvars'][host].get('ansible_distribution_version', 'unknown')
        task_file_path = result._task.get_path()
        output = result._result  # This gets the output of the failed task

        if 'roles/tests/' in task_file_path:
            # Extract the test name from the file path
            test_name = task_file_path.split('roles/tests/')[-1].split('/')[0]

            # Construct the test information for logging
            test_info = {
                'test_name'     : test_name,
                'failed_task'   : result._task.get_name(),
                'current_os'    : f"{current_os} {current_os_version}",
                'status'        : 'failed',
                'reason'        : output.get('msg', 'Unknown Error') 
            }
            self.log_data['test_results'].append(test_info)
        else:
            # Handle other failures not part of tests
            if not ignore_errors:
                failure_info = {
                    'host'      : host,
                    'task'      : result._task.get_name(),
                    'status'    : 'failed',
                    'error'     : output.get('msg', 'Unknown Error') 
                }
                self.log_data['ansible_failures'].append(failure_info)
        

    def v2_playbook_on_stats(self, stats):

        super(CallbackModule, self).v2_playbook_on_stats(stats)

        if self.log_path is None or self.log_filename is None:
            self._display.warning("Log path or filename is not set. Cannot save log file.")
            return
        
        if not os.path.exists(self.log_path):
            try:
                os.makedirs(self.log_path)
            except OSError as exc:
                self._display.warning(f"Could not create log directory: {exc}")
                return

        if not self.log_filename.endswith('.json'):
            self.log_filename += '.json'

        full_log_file_path = os.path.join(self.log_path, self.log_filename)

        try:
            with open(full_log_file_path, 'w') as log_file:
                json.dump(self.log_data, log_file, indent=4)
        except IOError as exc:
            self._display.warning(f"Could not write to log file: {exc}")