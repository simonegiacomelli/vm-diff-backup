#!/usr/bin/env python3

import datetime
import subprocess
import sys

FAIL = 1
SUCCESS = 0

vm_list = ['200']

for vm in vm_list:
    command = f'lvm_diff_backup.py {vm} >> log.txt'.split(' ')
    print(f'executing: {command}')
    result = subprocess.call(command)
    print(f'  result code: {result}')
