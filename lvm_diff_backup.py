#!/usr/bin/env python3

import datetime
import subprocess
import sys

if len(sys.argv) <= 1:
    print(f'Usage: {sys.argv[0]} VMID')
    exit(1)

vmid = sys.argv[1]
year_month = datetime.datetime.now().strftime("%Y-%m")
mount_point = '/mnt/qm-backup'
snapshot_device = '/dev/pve/qm-backup'
data_device = '/dev/pve/data'

source_folder = f'/mnt/qm-backup/images/{vmid}'
backup_folder = f'/mnt/lvdump/xdelta3/{year_month}/backup-{vmid}'

lines = f"""

#ignore_error=True
umount {mount_point}
lvremove -f {snapshot_device}

#ignore_error=False
mkdir -p {mount_point}

lvcreate -L50G -s -n {snapshot_device} {data_device}
mount {snapshot_device} {mount_point}                                                                                                               
xbackup.py --backupfolder={backup_folder} --sourcefolder={source_folder}                                                                                  

#ignore_error=True
umount {mount_point}
lvremove -f {snapshot_device}                                                                                                

""".splitlines(keepends=False)

ignore_error = False
commands = [line.strip() for line in lines if line.strip() != '']

for command in commands:
    if command.startswith('#'):
        exec(command[1:])
        continue

    print(f'executing: {command}')
    split = command.split(' ')
    res = subprocess.call(split)
    if res != 0:
        print(f'  ' + ('ignoring ' if ignore_error else '') + f'failed result code={res}')
        if not ignore_error:
            exit(1)

exit(0)
