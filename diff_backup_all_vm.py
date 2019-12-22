#!/usr/bin/env python3

import datetime
import os
import subprocess
from typing import IO, Dict

year_month = datetime.datetime.now().strftime("%Y-%m")
all_backup_folder = f'/mnt/lvdump/xdelta3/{year_month}'
mount_point = '/mnt/qm-backup'
snapshot_device = '/dev/pve/qm-backup'
data_device = '/dev/pve/data'
vm_list = '200 100 101 111 150'.split(' ')


class Tee:
    def __init__(self):
        self.files: Dict[str, IO] = {}
        self.indent = 0

    def log(self, line):
        line = (' ' * self.indent) + line
        print(line, flush=True)
        for file in self.files.values():
            file.write(line + '\n')
            file.flush()

    def __del__(self):
        for name in list(self.files.keys()):
            self.close(name)

    def close(self, name):
        file = self.files.pop(name)
        file.close()

    def add(self, name):
        basename = os.path.dirname(name)
        os.makedirs(basename, exist_ok=True)
        self.files[name] = open(name, 'w')

    def indent_inc(self):
        self.indent += 3

    def indent_dec(self):
        self.indent -= 3


tee = Tee()


def ok(command: str, silent=False):
    tee.indent_inc()
    tee.log(f'executing: {command}')
    p = subprocess.Popen(command.split(' '),
                         bufsize=0,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, b''):
        tee.log('  ' + line.decode('utf-8').rstrip())
    p.wait(10)
    result = p.returncode
    success = result == 0
    if not success and not silent:
        tee.log(f'command failed result code: {result}')
    tee.indent_dec()
    return success


def backup(vm_id, source_folder, backup_folder, data_device, snapshot_device, mount_point):
    def clean(msg):
        tee.log(msg)
        if ok(f'mountpoint -q {mount_point}', silent=True) and not ok(f'umount {mount_point}'):
            return False

        if ok(f'lvdisplay {snapshot_device}', silent=True) and not ok(f'lvremove -f {snapshot_device}'):
            return False

        return True

    if not clean('performing pre cleanup'):
        return False

    all_ok = ok(f'mkdir -p {mount_point}') and \
             ok(f'lvcreate -L50G -s -n {snapshot_device} {data_device}') and \
             ok(f'mount {snapshot_device} {mount_point}') and \
             ok(f'xbackup.py --backupfolder={backup_folder} --sourcefolder={source_folder}')

    tee.log('')
    tee.log(f'backup of {vm_id} ' + ('success' if all_ok else 'FAILED') + '  <------------')
    tee.log('')

    if not clean('performing post cleanup'):
        return False

    return all_ok


def backup_all():
    all_log_file = f'{all_backup_folder}/{dt_str()}-log-all.txt'
    tee.add(all_log_file)
    tee.log(f'Backup started at {dt_str()}')
    tee.log('')

    failed = []
    for vm_id in vm_list:
        source_folder = f'/mnt/qm-backup/images/{vm_id}'
        backup_folder = f'{all_backup_folder}/backup-{vm_id}'
        log_file = f'{backup_folder}/{dt_str()}-log.txt'
        tee.add(log_file)
        tee.log(f'start backup of {vm_id}')
        tee.indent_inc()
        if not backup(vm_id, source_folder, backup_folder, data_device, snapshot_device, mount_point):
            failed.append(vm_id)
        tee.indent_dec()

    success = len(failed) == 0
    import platform

    subject = f'soyoustart {platform.node()} backup'
    if not success:
        tee.log('')
        tee.log(f'Backup failed for: {failed}')
        tee.log('')
        subject = f'{subject} FAILED [{",".join(failed)}]'

    os.system(f'cat {all_log_file} | admin_email.py "{subject}"')
    return success


def dt_str():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


if __name__ == '__main__':
    exit(0 if backup_all() else 1)
