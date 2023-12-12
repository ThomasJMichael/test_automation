#!/usr/bin/env python3
import time
import os
import sys
import json
import argparse
from util import Util

parser = argparse.ArgumentParser()
parser.add_argument('--exampleconfig', type=str, default=f'{os.path.dirname(__file__)}/config/examples.json')
parser.add_argument('--osconfig', type=str, default=f'{os.environ["HOME"]}/.installed_config.json')
parser.add_argument('--uat_ip', type=str)
parser.add_argument('--uat_user', type=str)
parser.add_argument('--uat_pass', type=str)
parser.add_argument('--reverse', action='store_true')
args = parser.parse_args()

PATH = {
    '32'     : '/usr/local/gef/vme/bin32',
    '64'     : '/usr/local/gef/vme/bin64',
}
INFO_TOKEN = '---<COMMAND INFO>---'

Util.CONFIG_FILE = args.osconfig
Util.LOG_PATH = f'{os.path.dirname(os.path.realpath(__file__))}/logs/examples'
UTIL = Util()
STDOUT_LOG = UTIL.init_log('stdout')

def main():
    print('Let\'s go!')
    with open(args.exampleconfig, 'r') as f:
        cfg = json.load(f)

    if not UTIL.connected:
        print("Loading configuration from command line options")
        UTIL.connect(ip=args.uat_ip,
                     port=22,
                     u=args.uat_user,
                     pw=args.uat_pass)
    if not UTIL.connected:
        print("UAT Disabled! If you need to run dual board commands, supply a UAT")
        print("IP, username, and password on the command line. Do '-h' to see options")

    results = {}
    fails = 0
    _set_debug()
    for bits in ['32', '64']:
        for test_name in cfg:
            r_name = f'rev.{test_name}'
            _r_res = None
            if 'uat' in cfg[test_name] and not UTIL.connected:
                _print(f'UAT connection not detected: {test_name} disabled')
                continue
            _res = runner(cfg, test_name, bits)
            if 'reverse' in cfg[test_name] and cfg[test_name]['reverse']:
                _r_res = runner(cfg, test_name, bits, True)
            if scan_file_for_error(cfg[test_name], UTIL.read_log(_res['logs']['uut'])):
                _res['found_error_token'] = True
                _res['success'] = False
            if not _res['success']:
                fails += 1
            if test_name not in results:
                results[test_name] = {}
            if _r_res:
                if r_name not in results:
                    results[r_name] = {}
                results[r_name][bits] = _r_res

            results[test_name][bits] = _res
    _disable_debug()
    _save_dmesg()

    with open(f'{UTIL.LOG_PATH}/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print_results(results)

    _print(f'OVERALL STATUS:\t{"FAIL" if fails else "PASS"}\n')

    exit(fails)

def _set_debug():
    UTIL.run_loc("sudo modprobe -r capivme", quiet=True).wait()
    UTIL.run_loc("sudo modprobe capivme vme_debug=1", quiet=True)
    if UTIL.connected:
        UTIL.run_rem('sudo modprobe -r capivme', quiet=True).wait()
        UTIL.run_rem('sudo modprobe capivme vme_debug=1', quiet=True)

def _disable_debug():
    UTIL.run_loc("sudo modprobe -r capivme", quiet=True).wait()
    UTIL.run_loc("sudo modprobe capivme", quiet=True)
    if UTIL.connected:
        UTIL.run_rem('sudo modprobe -r capivme', quiet=True).wait()
        UTIL.run_rem('sudo modprobe capivme', quiet=True)

def _save_dmesg():
    print('Reading UUT journalctl')
    UTIL.run_loc('journalctl --no-pager --no-tail',
                 file=UTIL.init_log('journalctl.uut'),
                 quiet=True)
    if UTIL.connected:
        print('Reading UAT journalctl')
        UTIL.run_rem('journalctl --no-pager --no-tail',
                     file=UTIL.init_log('journalctl.uat'),
                     quiet=True)
    print('')

c = [24, 8, 8]      # column widths

def _print_header():
    _print('+', end='')
    for _c in c:
        _print('-' * _c, end='')
        _print('+', end='')
    _print('')

def print_results(results):
    print('RESULTS: \n')

    _print_header()
    _print(f'|{"Test": <{c[0]}}|'
           f'{"32 Pass": <{c[1]}}|'
           f'{"64 Pass": <{c[2]}}|'
           )
    _print_header()
    for test_name in results:
        _32pass = results[test_name]["32"]["success"]
        _32code = results[test_name]["32"]["actual_exit_code"]
        _32width= c[1]
        _64pass = results[test_name]["64"]["success"]
        _64code = results[test_name]["64"]["actual_exit_code"]
        _64width= c[1]

        _print(f'|{test_name: <{c[0]}}|'
               f'{"pass" if _32pass else _32code: <{_32width}}|'
               f'{"pass" if _64pass else _64code: <{_64width}}|'
               )
    _print_header()
    print('')

def _print_info(cmdinfo, testname, logfile):
    uutf = UTIL.get_log(logfile['uut'])
    uatf = UTIL.get_log(logfile['uat'])

    _print('> UUT PARAMS', file=uutf)
    _print(f'command:    {cmdinfo["cmd_formatted"]}', file=uutf)
    _print(f'timeout:    {cmdinfo["timeout"]}', file=uutf)
    _print(f'inputs:     {" > ".join(cmdinfo["inputs"])}', file=uutf)
    _print(f'exit codes: {cmdinfo["exit_code"]}', file=uutf)
    print(INFO_TOKEN, file=uutf)
    _print('---')
    if 'uat' in cmdinfo:
        _print('> UAT PARAMS', file=uatf)
        _print(f'command:    {cmdinfo["uat"]["cmd_formatted"]}', file=uatf)
        _print(f'timeout:    {cmdinfo["uat"]["timeout"]}', file=uatf)
        _print(f'inputs:     {" > ".join(cmdinfo["uat"]["inputs"])}', file=uatf)
        print(INFO_TOKEN, file=uatf)
        _print('---')

        if cmdinfo['reverse']:
            uutf_r = UTIL.get_log(logfile['uut_r'])
            uatf_r = UTIL.get_log(logfile['uat_r'])

            print('> UUT PARAMS', file=uutf_r)
            print(f'command:    {cmdinfo["cmd_formatted"]}', file=uutf_r)
            print(f'timeout:    {cmdinfo["timeout"]}', file=uutf_r)
            print(f'inputs:     {" > ".join(cmdinfo["inputs"])}', file=uutf_r)
            print(f'exit codes: {cmdinfo["exit_code"]}', file=uutf_r)
            print(INFO_TOKEN, file=uutf_r)

            print('> UAT PARAMS', file=uatf_r)
            print(f'command:    {cmdinfo["uat"]["cmd_formatted"]}', file=uatf_r)
            print(f'timeout:    {cmdinfo["uat"]["timeout"]}', file=uatf_r)
            print(f'inputs:     {" > ".join(cmdinfo["uat"]["inputs"])}', file=uatf_r)
            print(INFO_TOKEN, file=uatf_r)
    else:
        print('UNUSED', file=uatf)
    _print('')

def runner(cfg, testname, bits, reverse=False):
    cmdinfo = cfg[testname]
    path = PATH[bits]

    # fix cmdinfo object
    if 'inputs' not in cmdinfo:
        cmdinfo['inputs'] = []
    if 'timeout' not in cmdinfo:
        cmdinfo['timeout'] = "60"
    if 'exit_code' not in cmdinfo:
        cmdinfo['exit_code'] = 0
    if 'reverse' not in cmdinfo or 'uat' not in cmdinfo:
        cmdinfo['reverse'] = False
        reverse = False
    if not isinstance(cmdinfo['exit_code'], list):
        cmdinfo['exit_code'] = [cmdinfo['exit_code']]
    cmdinfo['cmd_formatted'] = (f'timeout {cmdinfo["timeout"]} '
                                f'{path}/{cmdinfo["cmd"]}')
    if not isinstance(cmdinfo['exit_code'], list):
        cmdinfo['exit_code'] = [cmdinfo['exit_code']]
    # fix UAT settings if pressent
    if 'uat' in cmdinfo:
        if 'inputs' not in cmdinfo['uat']:
            cmdinfo['uat']['inputs'] = []
        if 'timeout' not in cmdinfo['uat']:
            cmdinfo['uat']['timeout'] = cmdinfo['timeout']
        if 'exit' not in cmdinfo['uat']:
            cmdinfo['uat']['exit'] = []
        cmdinfo['uat']['cmd_formatted'] = (f'timeout {cmdinfo["uat"]["timeout"]} '
                                           f'{path}/{cmdinfo["uat"]["cmd"]}')

    # set up logfiles
    logfile = {
        'uut' : f'{testname}.uut',
        'uat' : f'{testname}.uat'
    }
    uutf = UTIL.init_log(logfile['uut'])
    uatf = UTIL.init_log(logfile['uat'])
    _print(f'==={testname} <{time.ctime()}>===', file=uutf)
    if reverse:
        _print('REVERSE')
    print(f'==={testname} <{time.ctime()}>===', file=uatf)
    if cmdinfo['reverse']:
        logfile['uut_r'] = f'reverse.{testname}.uut'
        logfile['uat_r'] = f'reverse.{testname}.uat'
        uutf_r = UTIL.init_log(logfile['uut_r'])
        uatf_r = UTIL.init_log(logfile['uat_r'])
        print(f'===Reverse {testname} <{time.ctime()}>===', file=uutf_r)
        print(f'===Reverse {testname} <{time.ctime()}>===', file=uatf_r)

    _print_info(cmdinfo, testname, logfile)

    exit_code = 0
    ctl = pre(cmdinfo, logfile, reverse)
    code1 = mid(cmdinfo, logfile, reverse)
    code2 = post(cmdinfo, logfile, ctl, reverse)
    exit_code = code1 + code2

    _print(f'exit code: {exit_code}', file=uutf)
    print(INFO_TOKEN, file=uutf)
    _print('')
    return {
        'cmd'                   : cmdinfo['cmd_formatted'],
        'inputs'                : " > ".join(cmdinfo['inputs']),
        'logs'                  : logfile,
        'uat_cmd'               : "" if 'uat' not in cmdinfo else cmdinfo['uat']['cmd_formatted'],
        'uat_inputs'            : "" if 'uat' not in cmdinfo else " > ".join(
                                      cmdinfo['uat']['inputs']
                                  ),
        'expected_exit_codes'   : cmdinfo['exit_code'],
        'actual_exit_code'      : exit_code,
        'found_error_token'     : False,
        'success'               : exit_code in cmdinfo['exit_code']
    }

def pre(cmdinfo, logfile, reverse=False):
    func = UTIL.run_rem if not reverse else UTIL.run_loc
    funcopts = {
        'quiet' : True,
        'file'  : UTIL.get_log(logfile['uat' if not reverse else 'uut_r']),
        'inputs': True
    }
    ctl = None
    if 'uat' in cmdinfo:
        _print(f'>>> {"UAT" if not reverse else "UUT"}')
        ctl = func(cmdinfo['uat']['cmd_formatted'], **funcopts)
        for inp in cmdinfo['uat']['inputs']:
            _print(f'> Sending "{inp}"')
            ctl.write(f'{inp}\n')
    return ctl

def mid(cmdinfo, logfile, reverse=False):
    func = UTIL.run_loc if not reverse else UTIL.run_rem
    funcopts = {
        'quiet' : True,
        'file'  : UTIL.get_log(logfile['uut' if not reverse else 'uat_r']),
        'inputs': True
    }
    _print(f'>>> {"UUT" if not reverse else "UAT"}')
    ctl = func(cmdinfo['cmd_formatted'], **funcopts)
    for inp in cmdinfo['inputs']:
        _print(f'> Sending "{inp}"')
        ctl.write(f'{inp}\n')
    ctl.read(file=funcopts['file'], quiet=True)
    print('---', file=funcopts['file'])
    print(f'EXIT_CODE: {ctl.returncode}', file=funcopts['file'])
    return ctl.returncode

def post(cmdinfo, logfile, ctl, reverse=False):
    func = UTIL.run_rem if not reverse else UTIL.run_loc
    funcopts = {
        'quiet' : True,
        'file'  : UTIL.get_log(logfile['uat' if not reverse else 'uut_r']),
        'inputs': True
    }
    ret = 0
    if 'uat' in cmdinfo:
        _print(f'>>> {"UAT" if not reverse else "UUT"}')
        for inp in cmdinfo['uat']['exit']:
            _print(f'> Sending "{inp}"')
            ctl.write(f'{inp}\n')
        ctl.read(file=funcopts['file'], quiet=True)
        ret = ctl.returncode
    return ret

# returns true if error token, false if no token or token not found
def scan_file_for_error(cmdinfo, outf):
    found = False
    if 'error_token' not in cmdinfo:
        pass
    elif not isinstance(cmdinfo['error_token'], list):
        raise ValueError('error_token must be an array')
    else:
        for line in [_line.rstrip('\n') for _line in outf]:
            if line == INFO_TOKEN:
                break
            for token in cmdinfo['error_token']:
                if token in line:
                    _print(f'> Found error token "{token}" in output')
                    found = True
    return found

def _print(prstr, **kwargs):
    prstr = str(prstr)
    if 'file' in kwargs:
        print(prstr)
    print(prstr, **kwargs)

    # always print to stdout.log
    kwargs.update({'file': STDOUT_LOG})
    print(prstr, **kwargs)

    sys.stdout.flush()

if __name__ == '__main__':
    main()
