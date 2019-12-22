#!/usr/bin/env python3

import os
import sys

from execute import ok

FAIL = 1
SUCCESS = 0

vm_list = ['200', '300']
folder = os.path.dirname(sys.argv[0])

failed = []
for vm in vm_list:
    if not ok(f'{folder}/lvm_diff_backup.py {vm}'):
        failed.append(vm)

if len(failed) > 0:
    print(f'This vm backup failed: {failed}')
    exit(FAIL)
else:
    exit(SUCCESS)
