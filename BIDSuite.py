# The following is a collection of functions for formatting MRI data into the BIDS standard format
# Authors:  Zachary Traylor; CNAPS Lab, LSU
#           Lauryn Burleigh; CNAPS Lab, LSU
#           Dr. Steven Greening; CNAPS Lab, LSU

from distutils.dir_util import copy_tree
import numpy as np
import shutil
import glob
import mmap
import csv
import sys
import os
import re
if sys.version_info[0] >= 3:
    raise Exception("Must be using Python 2")


def create_tree(path, sub_count):
    # This function creates a directory structure as denoted by the BIDS standard
    # By default, this script only creates the core elements of the bids format
    # Additional folders can be added to the function (see below)
    # **less than 1000 subjects is assumed**

    def help():
        print """
        This function creates a directory structure as denoted by the BIDS standard
        By default, this script only creates the core elements of the bids format
        Additional folders can be added to the function (see below)
        **less than 1000 subjects is assumed**    
        """

    if not path or not sub_count:
        help()

    # path = the ABSOLUTE destination path for directory structure (string)
    if path[-1:] == '/':
        path = path[:-1]
    # sub_count = the number of subjects (int)
    print "Creating folders..."
    subjects_count = range(int(sub_count) + 1)  # subjects is now a list from 1 to sub_count
    subjects_count.pop(0)
    for subject in subjects_count:
        if subject < 100:
            subject_string = '0' + str(subject)  # ensure 3 digit format (ex: 012)
            if subject < 10:
                subject_string = '0' + subject_string  # ensure 3 digit format (ex: 002)
        else:
            subject_string = str(subject)
        subject = subject_string
        # this makes the folder ex: ../sub-001
        if not os.path.exists(path + "/sub-" + subject):
            print "Creating directory tree for subject " + subject + "..."
            os.makedirs(path + "/sub-" + subject)
        # this makes a sub folder ex: ../sub01/scr
        if not os.path.exists(path + "/sub-" + subject + "/scr"):
            os.makedirs(path + "/sub-" + subject + "/scr")
        # this makes a sub folder ex: ../sub01/bh
        if not os.path.exists(path + "/sub-" + subject + "/bh"):
            os.makedirs(path + "/sub-" + subject + "/bh")
        # this makes a sub folder ex: ../func
        if not os.path.exists(path + "/sub-" + subject + "/func"):
            os.makedirs(path + "/sub-" + subject + "/func")
        # this makes a sub folder ex: ../anat
        if not os.path.exists(path + "/sub-" + subject + "/anat"):
            os.makedirs(path + "/sub-" + subject + "/anat")
        # this makes a sub folder ex: ../matlab_data
        if not os.path.exists(path + "/matlab_data"):
            os.makedirs(path + "/matlab_data")
        # this makes a sub folder ex: ../Participant_Biopac_Data
        if not os.path.exists(path + "/Participant_Biopac_Data"):
            os.makedirs(path + "/Participant_Biopac_Data")

    # example for additional sub folder:

    # this makes a sub folder ex: ../folder_name
    # if not os.path.exists(path + "/folder_name"):
    #   os.makedirs(path + "/folder_name")

    # this can be nested so as to make even more sub folders


def convert(regex, out_path):
    # This function makes an exact copy of the folder at "out_path" with participant IDs replaced with BIDS format
    # Example: 17121 -> sub-001
    # **less than 1000 subjects is assumed**
    # regex = the regular expression for your participant IDs (string)
    # out_path = the path to the target folder (string)
    # **Note: the function recursively renames ALL sub-files and folders containing the participant ID
    if out_path[-1:] == '/':
        out_path = out_path[:-1]
    # Ensure out_path is a directory

    def help():
        print """
        This function makes an exact copy of the folder at "out_path" with participant IDs replaced with BIDS format
        Example: 17121 -> sub-001
        **less than 1000 subjects is assumed**
        regex = the regular expression for your participant IDs (string)
        out_path = the path to the target folder (string)
        **Note: the function recursively renames ALL sub-files and folders containing the participant ID
        """

    if not regex or not out_path:
        help()

    def rename(path, partIDs):  # here we recursively go through and rename all occurrences of ids with subject numbers
        for root, folders, files in os.walk(path):
            for f in files:
                # first, handle all files in the current directory
                for i in partIDs:
                    if i in f:
                        print "file matched"
                        name = f.replace(i, partIDs[i])
                        os.rename(path + '/' + f, path + '/' + name)
            for folder in folders:
                rename(path + '/' + folder, partIDs)
                for k in partIDs:
                    if k in folder:
                        print "folder matched"
                        name = folder.replace(k, partIDs[k])
                        os.rename(path + '/' + folder, path + '/' + name)

    copy_path = out_path.rsplit('/', 1)[0] + "/my_dataset"
    copy_tree(out_path, copy_path)  # make a backup copy of ORIGINAL directory tree right next to it

    ids = []
    for folder in next(os.walk(out_path))[1]:  # for each folder in the directory
        if re.match(regex, folder) is not None:  # if the folder matches regex
            ids.append(folder)  # add each participant ID to the id array
        else:
            print "not a match"
    ids.sort()
    ids = [str(i) for i in ids]  # ids is now sorted and all strings for later concatenation
    partIDs = {}  # dictionary to hold id to sub conversions

    temp = range(len(ids) + 1)
    temp.pop(0)  # ignore the sub-000 case
    for j in temp:
        if j < 100:
            numstring = '0' + str(j)
            if j < 10:
                numstring = '0' + numstring
        else:
            numstring = str(j)
        partIDs[ids[j - 1]] = 'sub-' + numstring  # ensure BIDS format with padding for up to 999 participants

    rename(copy_path, partIDs)  # start the recursion

    with open("conversion.csv", 'wb') as out:
        wr = csv.writer(out, quoting=csv.QUOTE_ALL)
        for l in partIDs:
            wr.writerow([l, partIDs[l]])


def organize(partID, base_dir, scan_dir, rnames, dnames, scan_type):
    # This function takes the dicom data from the MRI scan, converts it to nifti format and stores the resulting files
    # base_dir = the home folder of the study (example: "../FCTM_S_Data") (string)
    # scan_dir = location of extracted MRI scan data (all of the Ser# folders) (string)
    # rnames = a list of names found in the lotus (.123) files to be replaces by their index equal in dnames
    # dnames = a list of replacement names for the rnames given by the MRI tech in the lotus (.123) files
    # partID = the participant ID (example: 17126)
    # scan_type = anatomical or functional MRI data (char, 'a' or 'f')

    def help():
        print """
        This function takes the dicom data from the MRI scan, converts it to nifti format and stores the resulting files"
        base_dir = the home folder of the study (example: "../FCTM_S_Data") (string)
        scan_dir = location of extracted MRI scan data (all of the Ser# folders) (string)
        rnames = a list of names found in the lotus (.123) files to be replaces by their index equal in dnames
        dnames = a list of replacement names for the rnames given by the MRI tech in the lotus (.123) files
        partID = the participant ID (example: 17126)
        scan_type = anatomical or functional MRI data (char, 'a' or 'f')
        """

    if not partID or not base_dir or not scan_dir or not rnames or not dnames or not scan_type:
        help()

    partID = str(partID)
    if scan_type == 'a':
        newdir = base_dir + '/' + partID + '/' + "anat"
    elif scan_type == 'f':
        newdir = base_dir + '/' + partID + '/' + "func"
    else:
        return "INVALID SCAN TYPE"

    if not os.path.exists(newdir):  # If the directory doesn't exist
        os.makedirs(newdir)  # Make the directory

    # Find all the .123 lotus files in the raw data
    fn = glob.glob("%s/%s/*/*.123" % (scan_dir, partID))

    # loop across each .123 file, make nii file from dicom data
    for run in fn:  # run is a path to the .123 file
        # split path
        rundirsplit = run.split('/')[-1]
        rundir = run[:-len(rundirsplit)]
        # Move to target folder (containing the .123 file)
        os.chdir(rundir)
        # open the file and search for run names
        f = open(rundirsplit)
        s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        # Loop through run names found
        for n in np.arange(0, len(rnames)):
            # s.find is a boolean function, returns -1 if false
            # cycles through list of run names
            if s.find(rnames[n]) != -1:  # if rnames[n] is found
                dname = dnames[n]
                # Rename dir to dname equivalent, create nii files
                exphasedir = scan_dir + '/' + partID + '/' + dname
                if not os.path.exists(exphasedir):
                    os.rename(rundir, exphasedir)
                # Run dcm2niix to convert
                os.system("dcm2niix -b y -ba y -z y {}".format(exphasedir))
                # find nii file
                src = glob.glob('*.gz')
                # copy file to 'func' or 'anat' folder, rename accordingly
                dst = newdir + '/' + dname + '.nii.gz'
                if not src:  # in case glob doesn't find anything, script continues
                    pass
                else:
                    if scan_type == 'a':
                        os.system("pydeface.py {}".format(src[0]))
                    shutil.move(src[0], dst)
                # find json file (created with dcm2niix)
                src = glob.glob('*.json')
                # copy file to 'func' or 'anat' folder, rename accordingly
                dst = newdir + '/' + dname + '.json'
                if not src:
                    pass
                else:
                    shutil.move(src[0], dst)
