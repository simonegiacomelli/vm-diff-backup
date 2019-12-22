#!/usr/bin/env python3

import os
import sys

from execute import ok

FAIL = 1
SUCCESS = 0

vm_list = ['200']

folder = os.path.dirname(sys.argv[0])
for vm in vm_list:
    ok(f'{folder}/lvm_diff_backup.py {vm}')
