import os
import subprocess
import sys
from pathlib import Path
import datetime


def log(line):
    print(line)


if len(sys.argv) <= 1:
    log(f'Usage: {sys.argv[0]} VMID')
    exit(1)

vmid = sys.argv[1]
year_month = datetime.datetime.now().strftime("%Y-%m")
mount_point = '/mnt/qm-backup'
snapshot_device = '/dev/pve/qm-backup'
data_device = '/dev/pve/data'

source_folder = f'/mnt/qm-backup/images/{vmid}'
backup_folder = f'/mnt/lvdump/xdelta3/{year_month}/backup-{vmid}'


def cmd(command, ignore_error=False):
    def execute():
        log(f'executing: {command}')
        res = subprocess.call(command.split(' '))
        if res != 0:
            log(f'  ' + 'ignoring ' if ignore_error else '') + 'failed result code={res}'
            if not ignore_error:
                return 1

    return execute


def wrap(*args):
    return [cmd(c) for c in args]


def main():
    init_fin = [cmd(f'umount {mount_point}', ignore_error=True),
                cmd(f'lvremove -f {snapshot_device}', ignore_error=True)]

    all_commands = init_fin + \
                   wrap(f'lvcreate -L50G -s -n {snapshot_device} {data_device}',
                        f'mkdir -p {mount_point}',
                        f'mount {snapshot_device} {mount_point}',
                        f'xbackup.py --backupfolder={backup_folder} --sourcefolder={source_folder}'
                        ) + \
                   init_fin

    for command in all_commands:
        if not command():
            exit(1)
    exit(0)


if __name__ == '__main__':
    main()
commands = f"""
umount {mount_point} #ignore_error 
lvremove -f {snapshot_device} #ignore_error

mkdir -p {mount_point}

lvcreate -L50G -s -n {snapshot_device} {data_device}
mount {snapshot_device} {mount_point}                                                                                                               
xbackup.py --backupfolder={backup_folder} --sourcefolder={source_folder}                                                                                  

umount {mount_point} #ignore_error
lvremove -f {snapshot_device} #ignore_error                                                                                                   

"""

