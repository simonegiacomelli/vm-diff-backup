#!/usr/bin/env python3

import datetime
import subprocess
import sys

FAIL = 1
SUCCESS = 0

vm_list = ['200']

for vm in vm_list:
    command = f'lvm_diff_backup.py {vm}'
    print(f'executing: {command}')
    with open('log.txt', 'w') as log:
        result = subprocess.call(command.split(' '), stdout=log, stderr=log)
    print(f'  result code: {result}')
