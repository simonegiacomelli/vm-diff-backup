#!/usr/bin/python

"""
Created on 10/feb/2013

ver 1.1. 2017-07-10 support for sparse files
@author: Simone
"""

'''
premise a:
    given a 'backup-for-diff' and 'backup' and 'vm' folders the software should check the 'backup' folder
    if the backup meet the requirements ( last-patch-size > x% or patch-count > n or no-backups ) the software should 
    copy the vm files in 'backup'
    it the requirements are not met the vm files will be copied in 'backup-for-diff' then a delta should be performed 
    from the last of 'backup'
     
    
    backup-for-diff
        vm-101 -\
            2013-02-10_22-10-34
            2013-02-11_22-10-33
            2013-02-12_22-10-35        
        vm-102 -\
            2013-02-11_22-10-28
    
    backup -\
        vm-101 -\
            2013-02-09_22-10-32
            2013-02-10_22-10-34-patch-from-2013-02-09_22-10-32
            2013-02-11_22-10-33-patch-from-2013-02-09_22-10-32
            2013-02-12_22-10-35-patch-from-2013-02-09_22-10-32
            2013-02-13_22-10-31
            2013-02-14-22-10-30-patch-from-2013-02-13_22-10-31
        vm-102 -\
            2013-02-10_22-10-28
            2013-02-11_22-10-28-patch-from-2013-02-10_22-10-28
     
*)  given a 'old' and a 'new' folder the software should create a third folder 'old-to-new-patch'
    given a 'old' and a 'old-to-new-patch' folder the software should create a third folder 'new'
    
    the content of 'old-to-new-patch' should contain:
    - both: xdelta patch for files present in 'old' and 'new'
    - only-new: whole file for those present only in 'new'
    - only-old: meta file describing the need to remove files   
     
*)  interface XdirInspector that given a 'old' and 'new' folder gives 
    you files in 'both' 'only old' 'only new' sides.
    interface should expose 'old' and 'new' values 
    
*)  interface XmakePatch that given a XdirInspector instance  and a 'delta' dir should
    generate correct 'cmdLine'  
    -for patch xdelta3.exe -e -s old_file new_file delta_file
    -
   
    for testing purpose, a mock will be used as XdirInspector instance, so XdeltaPath 
    output should be predictable. 
    
'''

import shutil
import os
from distutils import dir_util
from optparse import OptionParser
import sys
import datetime
import subprocess


class xrestore(object):
    """
    classdocs
    """

    def __init__(self, args=None):
        if args is None:
            self._args = sys.argv[1:]
        else:
            self._args = args[:]

        self._parser = OptionParser()
        self._parser.add_option("-b", "--backupfolder", action="store", type="string", dest="backupfolder",
                                help="folder where resides full backup and patch backup")
        self._parser.add_option("-r", "--restorefolder", action="store", type="string", dest="restorefolder",
                                help="the folder to restore to")
        self._parser.add_option("--delete-restorefolder", action="store_true")

        (self._opt, self._leftArgs) = self._parser.parse_args(self._args)

    def __decodeDifferentialName(self, name):
        if "-patch-from-" not in name:
            return False, None, None
        parts = name.split("-patch-from-")
        if len(parts) != 2 or not self.__validFullBackupPattern(parts[0]) or not self.__validFullBackupPattern(
                parts[1]):
            return False, None, None
        return True, parts[0], parts[1]

    def __validDifferentialName(self, name):
        (ok, fullDatetime, diffDatetime) = self.__decodeDifferentialName(name)
        return ok

    def __validFullBackupPattern(self, pattern):
        try:
            self.__fullBackupStringToDatetime(pattern)
        except ValueError:
            return False
        return True

    def __fullBackupStringToDatetime(self, pattern):
        return datetime.datetime.strptime(pattern, "%Y-%m-%d_%H-%M-%S")

    def restore(self):

        if self._opt.backupfolder is None or self._opt.restorefolder is None:
            self._parser.print_help()
            return
        restore_folder = self._opt.restorefolder

        backupNameListUnfiltered = os.listdir(self._opt.backupfolder)
        differentialBackupNameList = [el for el in backupNameListUnfiltered
                                      if self.__validDifferentialName(el)]
        if len(differentialBackupNameList) == 0:
            print("No patch to restore")
            return
        differentialBackupNameList.sort(key=None, reverse=True)
        differentialBackupFolderName = differentialBackupNameList[0]

        if os.path.exists(restore_folder):
            if self._opt.delete_restorefolder:
                print('recursive remove restore folder [%s]' % restore_folder)
                import shutil
                shutil.rmtree(restore_folder)
            else:
                raise Exception("restore path already exist! " + restore_folder)

        os.makedirs(restore_folder, exist_ok=True)

        ok, diffFolder, fullFolder = self.__decodeDifferentialName(differentialBackupFolderName)

        for patch in os.listdir(os.path.join(self._opt.backupfolder, differentialBackupFolderName)):
            if not patch.endswith(".patch"):
                continue
            full = patch[:-6];
            deltaPath = os.path.join(self._opt.backupfolder, differentialBackupFolderName, patch)
            fullPath = os.path.join(self._opt.backupfolder, fullFolder, full)
            destPath = os.path.join(restore_folder, full)
            if not os.path.exists(restore_folder):
                os.mkdir(restore_folder)

            # apply patch //xdelta3.exe -d -s old_file delta_file decoded_new_file
            args = ["xdelta3", "-v", "-d", "-s"
                , fullPath
                , deltaPath
                , destPath]
            print(args)
            res = subprocess.call(args)
            if res != 0:
                raise Exception("xdelta3 return code failed: " + str(res))


if __name__ == "__main__":
    # import sys;sys.argv = ['', '--unittest']
    ist = xrestore()
    ist.restore()
