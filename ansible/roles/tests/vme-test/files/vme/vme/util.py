#!/usr/bin/env python3
import os
import json
import stat
import time
import shutil
import subprocess
import paramiko

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

class Util:
    client = None
    connected = False
    DEBUG = False
    CONFIG_FILE = f'{os.environ["HOME"]}/.installed_config.json'
    LOG_PATH = f'{SCRIPT_PATH}/logs'
    LOG_FILES = {}

    def __init__(self, **kwargs):
        if os.path.isdir(self.LOG_PATH):
            shutil.rmtree(self.LOG_PATH)
        os.makedirs(self.LOG_PATH)
        if self.DEBUG:
            print(f'Initialized logs at {self.LOG_PATH}')
        self.connect(**kwargs)

    def __del__(self):
        for logf in self.LOG_FILES:
            self.close_log(logf)

    def close_log(self, logname):
        if self.DEBUG:
            print(f'Closing log for {logname}...')
        self.LOG_FILES[logname].close()

    def init_log(self, logname):
        _path = f'{self.LOG_PATH}/{logname}.log'
        try:
            self.LOG_FILES[logname].close()
        except:
            pass
        if self.DEBUG:
            print(f'Opening log {_path}...')
        self.LOG_FILES[logname] = open(_path, 'a')
        return self.LOG_FILES[logname]

    def get_log(self, logname):
        if logname not in self.LOG_FILES:
            f = self.init_log(logname)
        else:
            f = self.LOG_FILES[logname]
        return f

    def read_log(self, logname):
        _path = f'{self.LOG_PATH}/{logname}.log'
        if os.path.isfile(_path):
            try:
                self.LOG_FILES[logname].close()
            except:
                pass
            if self.DEBUG:
                print(f'Opening log {_path} for reading...')
            self.LOG_FILES[logname] = open(_path, 'r')
            return self.LOG_FILES[logname]

    def connect(self, **kwargs):
        opts = {}
        if os.path.isfile(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as conf:
                self.cfg = json.load(conf)
            opts['ip'] = self.cfg['uat']['ip_address']
            opts['port'] = self.cfg['uat']['port']
            opts['u'] = self.cfg['uat']['dev_username']
            opts['pw'] = self.cfg['uat']['dev_password']
        opts.update(kwargs)

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.load_host_keys('/dev/null')
        try:
            self.client.connect(opts['ip'], opts['port'], opts['u'], opts['pw'])
            self.connected = True
        except:
            print("FAILED TO CONNECT")
            self.connected = False

    def disconnect(self):
        self.client.close()

    def copy_files(self, loc, rem, **kwargs):
        opts = {
            'ftpc'  : None
        }
        opts.update(kwargs)
        toplevel = False

        cnum = 0
        if self.connected:
            if not opts['ftpc']:
                opts['ftpc'] = self.client.open_sftp()
                toplevel = True
            if not rem.startswith('./') and not rem.startswith('/'):
                rem = f'./{rem}'
            made = []
            for p in rem.split('/')[0:-1]:
                made.append(p)
                path = '/'.join(made)
                try:
                    opts['ftpc'].mkdir(path)
                except:
                    pass
            if os.stat(loc).st_mode & stat.S_IFDIR:
                if os.path.basename(rem) in opts['ftpc'].listdir(os.path.dirname(rem)):
                    self.client.exec_command(f'rm -rf {rem}')[1].channel.recv_exit_status()
                opts['ftpc'].mkdir(rem)
                for lfile in os.listdir(loc):
                    cnum += self.copy_files(f'{loc}/{lfile}', f'{rem}/{lfile}', **opts)
            else:
                perm = os.stat(loc).st_mode & 0o777
                opts['ftpc'].put(loc, rem)
                opts['ftpc'].chmod(rem, perm)
                cnum = 1
        else:
            print("Client is not connected. Please reinitialize.")
            cnum = -1

        if toplevel:
            opts['ftpc'].close()
        return cnum

    def run_rem(self, cmd, **kwargs):
        opts = {
            'quiet' : False,
            'file'  : None,
            'inputs': False
        }
        opts.update(kwargs)

        code = -1
        sout = None
        sin = None

        if self.connected:
            sin, sout, serr = self.client.exec_command(f'{cmd} 2>&1')
        else:
            print("Client is not connected. Please reinitialize.")
            code = -1
        return CTL(sout, sin)

    def run_loc(self, cmd, **kwargs):
        opts = {
            'quiet' : False,
            'file'  : None,
            'inputs': False,
        }
        opts.update(kwargs)
        code = -1
        stdout = ''
        p = subprocess.Popen(cmd.split(),
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             universal_newlines=True)
        return CTL(p.stdout, p.stdin, p)

class CTL:
    controller = None
    stdout = None
    stdin = None
    finished = False
    returncode = -1

    def __init__(self, stdout, stdin, controller=None):
        if stdout == None or stdin == None:
            print(f'Invalid stdout or stdin: out={stdout} in={stdin}')
        self.stdout = stdout
        self.stdin = stdin
        self.controller = controller

    def wait(self):
        if self.controller:
            self.controller.wait()
            self.returncode = self.controller.returncode
        else:
            self.returncode = self.stdout.channel.recv_exit_status()

        self.finished = True
        return self.returncode

    def write(self, _str, **kwargs):
        opts = {
            'delay' : 0.05
        }
        opts.update(kwargs)
        try:
            self.stdin.write(_str)
            self.stdin.flush()
        except:
            print('Couldn\'t flush input!')
        finally:
            time.sleep(opts['delay'])

    def read(self, **kwargs):
        opts = {
            'file'  : None,
            'quiet' : False
        }
        opts.update(kwargs)
        stdout = ''

        if not self.finished:
            self.wait()

        for line in iter(lambda: self.stdout.readline(), ""):
            if not opts['quiet']:
                print(line, end='')
            if opts['file']:
                print(line, end='', file=opts['file'])
            stdout = f'{stdout}{line}'
        return stdout

