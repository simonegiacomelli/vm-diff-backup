#!/usr/bin/env python3

import os
import sys

from lvm_diff_backup import Backup
from execute import FAIL, SUCCESS

vm_list = ['200', '300']

folder = os.path.dirname(sys.argv[0])

failed = []
for vm in vm_list:
    backup = Backup(vm)
    if not backup.execute():
        failed.append(vm)

if len(failed) > 0:
    print(f'This vm backup failed: {failed}')
    exit(FAIL)
else:
    exit(SUCCESS)
