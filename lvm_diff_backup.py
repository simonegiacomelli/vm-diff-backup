#!/usr/bin/env python3

import datetime
import subprocess
import sys
from execute import ok

FAIL = 1
SUCCESS = 0

if len(sys.argv) <= 1:
    print(f'Usage: {sys.argv[0]} VMID')
    exit(FAIL)

if sys.argv[1] == 'test':
    def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)


    print('test mode')
    import time

    eprint('this goes to stderr')
    print('wait some...')
    time.sleep(0.5)
    ok('du -h -d 1')
    print('done')
    exit(int(sys.argv[2]))

vmid = sys.argv[1]
year_month = datetime.datetime.now().strftime("%Y-%m")
mount_point = '/mnt/qm-backup'
snapshot_device = '/dev/pve/qm-backup'
data_device = '/dev/pve/data'

source_folder = f'/mnt/qm-backup/images/{vmid}'
backup_folder = f'/mnt/lvdump/xdelta3/{year_month}/backup-{vmid}'


def clean(msg):
    print(msg)
    if ok(f'mountpoint -q {mount_point}', silent=True) and not ok(f'umount {mount_point}'):
        return False

    if ok(f'lvdisplay {snapshot_device}', silent=True) and not ok(f'lvremove -f {snapshot_device}'):
        return False

    return True


def main():
    if not clean('performing pre cleanup'):
        return FAIL

    all_ok = ok(f'mkdir -p {mount_point}') and \
             ok(f'lvcreate -L50G -s -n {snapshot_device} {data_device}') and \
             ok(f'mount {snapshot_device} {mount_point}') and \
             ok(f'xbackup.py --backupfolder={backup_folder} --sourcefolder={source_folder}')
    print('')
    print(f'backup of {vmid} ' + ('success' if all_ok else 'FAILED') + '  <------------')
    print('')

    if not clean('performing post cleanup'):
        return FAIL

    return SUCCESS if all_ok else FAIL


if __name__ == '__main__':
    exit(main())
