#!/usr/bin/env python3

"""

ver 1.1. 2017-07-10 support for sparse files
ver 1.0. 2013-02-10 initial version
@author: Simone
"""

'''
how it works:
    given a folders 'backup-for-diff', 'backup' and 'vm' the script checks the 'backup' folder
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


class xbackup(object):

    def __init__(self, args=None):
        if args is None:
            self._args = sys.argv[1:]
        else:
            self._args = args[:]

        self._parser = OptionParser()
        self._parser.add_option("-b", "--backupfolder", action="store", type="string", dest="backupfolder",
                                help="destination folder for full backup and patch backup")
        self._parser.add_option("-s", "--sourcefolder", action="store", type="string", dest="sourcefolder",
                                help="folder to backup")
        self._parser.add_option("-t", "--timeis", action="store", type="string", dest="timeis",
                                help="specify current time in format yyyy-MM-dd_hh-mm-ss")
        # not tested 
        self._parser.add_option("--unittest", action="callback", callback=self.__runTests)

        (self._opt, self._leftArgs) = self._parser.parse_args(self._args)

    def __runTests(self, option, opt, value, parser):
        unittest.main(argv=sys.argv[:1])

    def __validFullBackupPattern(self, pattern):
        try:
            self.__fullBackupStringToDatetime(pattern)
        except ValueError:
            return False
        return True

    def __fullBackupStringToDatetime(self, pattern):
        return datetime.datetime.strptime(pattern, "%Y-%m-%d_%H-%M-%S")

    def __copyrecursively(self, source_folder, destination_folder):
        print("source=====" + source_folder)
        print("dest=====" + destination_folder)
        for root, dirs, files in os.walk(source_folder):
            for item in dirs:
                src_path = os.path.join(root, item)
                dst_path = os.path.join(destination_folder, src_path.replace(source_folder, ""))
                print("file dst_path====" + dst_path)
                if not os.path.exists(dst_path):
                    os.mkdir(dst_path)
            for item in files:
                src_path = os.path.join(root, item)
                dst_path = os.path.join(destination_folder, src_path.replace(source_folder, ""))
                print("dir dst_path====" + dst_path)
                shutil.copy2(src_path, dst_path)

    def backup(self):

        if self._opt.backupfolder is None or self._opt.sourcefolder is None:
            self._parser.print_help()
            return

        newBackupFolderName = self._opt.timeis
        if newBackupFolderName is None:
            newBackupFolderName = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        backupNameListUnfiltered = os.listdir(self._opt.backupfolder)
        fullBackupNameList = [el for el in backupNameListUnfiltered
                              if self.__validFullBackupPattern(el) and el < newBackupFolderName]

        if len(fullBackupNameList) == 0:
            newBackupFolderPath = self._opt.backupfolder + "/" + newBackupFolderName
            os.mkdir(newBackupFolderPath)
            if len(os.listdir(self._opt.sourcefolder)) > 0:
                cmd = "cp -r '" + self._opt.sourcefolder + "/'* '" + newBackupFolderPath + "'"
                os.system(cmd)
            return

        fullBackupNameList.sort(cmp=None, key=None, reverse=True)
        fullBackupFolderName = fullBackupNameList[0]
        fullBackupFolderPath = self._opt.backupfolder + "/" + fullBackupFolderName

        newBackupFolderPath = self._opt.backupfolder + "/" + newBackupFolderName + "-patch-from-" + fullBackupFolderName
        os.mkdir(newBackupFolderPath)

        fullBackupFileNamesLis = os.listdir(fullBackupFolderPath)
        fullBackupFileNamesSet = set(fullBackupFileNamesLis)
        sourceFolderFileNamesSet = set(os.listdir(self._opt.sourcefolder))

        sourceFileNamesNewSet = sourceFolderFileNamesSet - fullBackupFileNamesSet
        for sourceFileName in list(sourceFileNamesNewSet):
            shutil.copy2(self._opt.sourcefolder + "/" + sourceFileName, newBackupFolderPath + "/" + sourceFileName)

        fullBackupFileNamesRemovedSet = fullBackupFileNamesSet - sourceFolderFileNamesSet
        for removed in fullBackupFileNamesRemovedSet:
            touch = open(newBackupFolderPath + "/" + removed + ".wasremoved", "w")
            touch.close()

        changedFileNamesSet = fullBackupFileNamesSet & sourceFolderFileNamesSet
        for changed in changedFileNamesSet:
            res = subprocess.call(["xdelta3", "-e", "-s"
                                      , fullBackupFolderPath + "/" + changed
                                      , self._opt.sourcefolder + "/" + changed
                                      , newBackupFolderPath + "/" + changed + ".patch"])
            if res != 0:
                raise Exception("xdelta3 return code failed: " + str(res))


import unittest
import os.path
import tempfile
import time
import datetime
import sys


class xbackupTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNoBackupAndOneFileInSourceAndTimeMock_ShouldCreateBackupFolderWithExpectedFolderName(self):
        sourceFol = self.__prepareTempFolder("source")
        backupFol = self.__prepareTempFolder("backup")

        folder = "2013-06-25_23-59-58"

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', folder])
        target.backup()

        backupFolLis = os.listdir(backupFol)

        self.assertEquals(set([folder]), set(backupFolLis))

    def testNoBackupAndOneFileInSourceAndNoTimeMock_ShouldCreateBackupFolderWithExpectedMask(self):
        sourceFol = self.__prepareTempFolder("source")
        backupFol = self.__prepareTempFolder("backup")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol])
        target.backup()

        backupFolLis = os.listdir(backupFol)

        self.assertEqual(1, len(backupFolLis))

        datetime.datetime.strptime(backupFolLis[0], "%Y-%m-%d_%H-%M-%S")

    def testOneFullBackupSingleFile_ShouldCreateBackupWithCorrectFolderNameAndXDeltaPatch(self):

        (sourceFol, nouse) = self.__prepareTempFolderAndFile("source", "disk.txt", "short content of file -mod-")
        (backupFol, nouse) = self.__prepareTempFolderAndFile("backup", "2013-07-11_10-59-58/disk.txt",
                                                             "short content of file")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', "2013-07-12_08-01-02"])
        target.backup()

        newBackupFolder = list(set(os.listdir(backupFol)) - set(["2013-07-11_10-59-58"]))

        self.assertEqual(1, len(newBackupFolder))
        self.assertEqual("2013-07-12_08-01-02-patch-from-2013-07-11_10-59-58", newBackupFolder[0])

        newBackupFileLis = list(set(os.listdir(backupFol + "/" + newBackupFolder[0])))

        self.assertEqual(set(["disk.txt.patch"]), set(newBackupFileLis))

    def testOneFullBackupWithTwoFiles_ShouldCreateBackupWithCorrectFolderNameAndXDeltaPatch(self):
        backupFol = self.__prepareTempFolder("backup")
        self.__prepareFile(backupFol, "2013-05-25_10-30-00/disk1.txt", "disk1 content")
        self.__prepareFile(backupFol, "2013-05-25_10-30-00/disk2.txt", "disk2 content")

        sourceFol = self.__prepareTempFolder("source")
        self.__prepareFile(sourceFol, "disk1.txt", "disk1 content -mod-")
        self.__prepareFile(sourceFol, "disk2.txt", "disk2 content -mod-")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', "2013-05-26_11-40-00"])
        target.backup()

        expectedFiles = set(["disk1.txt.patch", "disk2.txt.patch"])
        actualFiles = set(os.listdir(backupFol + "/2013-05-26_11-40-00-patch-from-2013-05-25_10-30-00"))

        self.assertEquals(expectedFiles, actualFiles)

    def testGarbageInBackupFolder_ShouldIgnoreGarbageAndCreateFullBackup(self):
        (sourceFol, nouse) = self.__prepareTempFolderAndFile("source", "disk.txt", "content of file")

        backupFol = self.__prepareTempFolder("backup")
        os.makedirs(backupFol + "/garbage1")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol])
        target.backup()

        expectedBackup = list(set(os.listdir(backupFol)) - set(["garbage1"]))

        self.assertEqual(1, len(expectedBackup))

        expectedFileLis = os.listdir(backupFol + "/" + expectedBackup[0])

        self.assertEqual(set(["disk.txt"]), set(expectedFileLis))

    def testOneFileFullBackpAndInSourceANewFileExist_ShouldCreatePatchForChangedFileAndCopyNewFile(self):

        sourceFol = self.__prepareTempFolder("source")
        self.__prepareFile(sourceFol, "disk.txt", "short content of file -mod-")
        self.__prepareFile(sourceFol, "newdisk.txt", "new file")

        (backupFol, nouse) = self.__prepareTempFolderAndFile("backup", "2013-07-11_10-12-13/disk.txt",
                                                             "short content of file")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', "2013-07-13_07-03-04"])
        target.backup()

        newBackupFileSet = set(os.listdir(backupFol + "/2013-07-13_07-03-04-patch-from-2013-07-11_10-12-13"))
        self.assertEquals(set(["disk.txt.patch", "newdisk.txt"]), newBackupFileSet)

    def testManyFullBackupInFolder_ShouldUseMostRecentFullBackupForDiff(self):

        backupFol = self.__prepareTempFolder("backup")
        self.__prepareFile(backupFol + "/2013-07-11_08-00-00", "disk.txt", "content")
        self.__prepareFile(backupFol + "/2013-07-12_09-00-00", "disk.txt", "content")
        self.__prepareFile(backupFol + "/2013-07-13_10-00-00", "disk.txt", "content")

        (sourceFol, nouse) = self.__prepareTempFolderAndFile("source", "disk.txt", "content-source")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', "2013-07-14_12-00-00"])
        target.backup()

        expectedBackupFolder = backupFol + "/2013-07-14_12-00-00-patch-from-2013-07-13_10-00-00";
        self.assertTrue(os.path.exists(expectedBackupFolder)
                        , "expected folder was not found. actual listdir: " + str(os.listdir(backupFol)))

    def testManyFullBackupInFolderAndSpecifyMiddleTime_ShouldUseCorrectFullBackupForDiff(self):

        backupFol = self.__prepareTempFolder("backup")
        self.__prepareFile(backupFol + "/2013-07-11_08-00-00", "disk.txt", "content")
        self.__prepareFile(backupFol + "/2013-07-12_09-00-00", "disk.txt", "content")
        self.__prepareFile(backupFol + "/2013-07-13_10-00-00", "disk.txt", "content")

        (sourceFol, nouse) = self.__prepareTempFolderAndFile("source", "disk.txt", "content-source")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', "2013-07-12_15-00-00"])
        target.backup()

        expectedBackupFolder = backupFol + "/2013-07-12_15-00-00-patch-from-2013-07-12_09-00-00";
        self.assertTrue(os.path.exists(expectedBackupFolder)
                        , "expected folder was not found. actual listdir: " + str(os.listdir(backupFol)))

    def testOneMissingFileFromPrevFullBackup_ShouldCreateMetaFileForDeletion(self):
        (backupFol, nouse) = self.__prepareTempFolderAndFile("backup", "2013-07-18_10-00-00/disk1.txt",
                                                             "will-be-deleted")
        sourceFol = self.__prepareTempFolder("source")

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', "2013-07-19_15-00-00"])
        target.backup()

        actualFile = set(os.listdir(backupFol + "/2013-07-19_15-00-00-patch-from-2013-07-18_10-00-00"))

        self.assertEquals(set(["disk1.txt.wasremoved"]), actualFile)

    #    def testPatchOfOneChangedFileAndApplyPatch_ShouldGenerateOriginalFolder(self):
    #        raise NotImplemented("creare un'altro batch? tipo xrestore?")

    def testNoArgsOrWrongArgs_ShouldPrintHelp(self):
        target = xbackup([])
        target.backup()

        target = xbackup(['--backupfolder', self.__prepareTempFolder("backup")])
        target.backup()

    def testBackupOnSparseFile_shouldNotExpandFileOnCopy(self):
        (sourceFol, sparseFile) = self.__prepareTempFolderAndFile("source", "sparse.txt", "", 200000)

        backupFol = self.__prepareTempFolder("backup")
        folder = "2013-06-25_23-59-58"

        target = xbackup(['--backupfolder', backupFol, '--sourcefolder', sourceFol, '--timeis', folder])
        target.backup()

        sourceBlocks = os.stat(sparseFile).st_blocks
        destBlocks = os.stat(backupFol + "/" + folder + "/sparse.txt").st_blocks
        self.assertEqual(sourceBlocks, destBlocks)

    def __prepareTempFolder(self, suffix):
        fold = tempfile.mkdtemp(suffix="-" + suffix, prefix="xdeltadir test-")
        return fold

    def __prepareFile(self, fold, name, content=None, size=None):
        filepath = fold + '/' + name
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        tmpfile = open(filepath, "w")
        if content is not None:
            tmpfile.write(content)
        if size is not None:
            tmpfile.truncate(size)
        tmpfile.close()
        return filepath

    def __prepareTempFolderAndFile(self, suffix, name, content, size=None):
        fold = self.__prepareTempFolder(suffix)
        tmpfile = self.__prepareFile(fold, name, content, size)
        return fold, tmpfile


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    ist = xbackup()
    ist.backup()
