#!/usr/bin/env python3

import datetime
import subprocess
import sys
from execute import ok, FAIL, SUCCESS


class Backup:
    def __init__(self, vm_id):
        self.vm_id = vm_id
        self.year_month = datetime.datetime.now().strftime("%Y-%m")
        self.mount_point = '/mnt/qm-backup'
        self.snapshot_device = '/dev/pve/qm-backup'
        self.lv_device = '/dev/pve/data'

        self.source_folder = f'/mnt/qm-backup/images/{vm_id}'
        self.backup_folder = f'/mnt/lvdump/xdelta3/{self.year_month}'

        self.vm_backup_folder = f'{self.backup_folder}/backup-{vm_id}'

    def clean(self, msg):
        print(msg)
        if ok(f'mountpoint -q {self.mount_point}', silent=True) and not ok(f'umount {self.mount_point}'):
            return False

        if ok(f'lvdisplay {self.snapshot_device}', silent=True) and not ok(f'lvremove -f {self.snapshot_device}'):
            return False

        return True

    def execute(self):
        if not self.clean('performing pre cleanup'):
            return False

        all_ok = ok(f'mkdir -p {self.mount_point}') and \
                 ok(f'lvcreate -L50G -s -n {self.snapshot_device} {self.lv_device}') and \
                 ok(f'mount {self.snapshot_device} {self.mount_point}') and \
                 ok(f'xbackup.py --backupfolder={self.vm_backup_folder} --sourcefolder={self.source_folder}')
        print('')
        print(f'backup of {self.vm_id} ' + ('success' if all_ok else 'FAILED') + '  <------------')
        print('')

        if not self.clean('performing post cleanup'):
            return False

        return all_ok


if __name__ == '__main__':

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

    backup = Backup(sys.argv[1])
    exit(SUCCESS if backup.execute() else FAIL)
