#!/usr/bin/env python3

import datetime
import subprocess
import sys
import os

FAIL = 1
SUCCESS = 0

vm_list = ['200']

folder = os.path.dirname(sys.argv[0])
for vm in vm_list:

    command = f'{folder}/lvm_diff_backup.py {vm}'
    print(f'executing: {command}')
    p = subprocess.Popen(command.split(' '),
                         bufsize=0,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, b''):
        print('  ' + line.decode('utf-8').rstrip())
    p.wait(10)
    print(f'  result code: {p.returncode}')
