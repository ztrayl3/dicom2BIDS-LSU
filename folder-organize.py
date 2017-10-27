#!/usr/bin/python

# This determines what each scan folder contains based on the label the MRI tech gave the scan
# It renames the folder accordingly
# It then transforms the nii to dcm and places in a 'func' folder created for each participant
# It was made to organize the Pennington imaging data

# Execute via: ipython folder-organize.py

import os
import glob
import shutil
import mmap
import numpy as np

# Study and data directory #
studydir = '/home/burleigh/Desktop/FCTM_S_Data'  # Where all study data is
datadir = '/home/burleigh/Desktop/FCTM_S_Data/Scans_extract'  # Where extracted scans are

# List of run names #
# If name in .123 file is 'SET 1 HAB fMRI 1', label folder as 'A_hab_1'
runnames = ['SET 2 TASK fMRI 1', 'SET 2 TASK fMRI 2', 'SET 2 TASK fMRI 3', 'SET 2 TASK fMRI 4', 'SET 2 TASK fMRI 5', 'SET 2 TASK fMRI 6']
dirnames = ['B_task_1', 'B_task_2', 'B_task_3', 'B_task_4', 'B_task_5', 'B_task_6']
#runnames = ['MPRAGE']
#dirnames = ['T1']


# Data type #
# Use 'func' when transforming fMRI/task scans
# Use 'anat' when transforming T1 scans
datatype = 'func'
#datatype = 'anat'

# Find subject dirs #
# Find all folders labeled '1xxxx' [follows CNAPs ID system]
subdirs = glob.glob("%s/1[0-9][0-9][0-9][0-9]" % datadir)


for d in np.arange(0, len(subdirs)):
	splitdir = subdirs[d].split('/')  # Divide path by '/'
	subnum = splitdir[-1]  # Grab last element in list for subject number
	# cd to subj
	os.chdir(datadir + '/' + subnum)
	# Create folder for nii.gz file
	newstudydir = studydir + '/' + subnum + '/' + datatype
	if not os.path.exists(newstudydir):  # If the directory doesn't exist
		os.makedirs(newstudydir)  # Make the directory	
	# Find all the text files
	fn = glob.glob("%s/%s/*/*.123" % (datadir, subnum))
	# loop across each file, make nii file, mkdir
	for run in fn:	
		# split directory
		rundirsplit = run.split('/')[-1]
		rundir = run[:-len(rundirsplit)]
		# Move to desired data
		os.chdir(rundir)
		# Find the text file and search
		f = open(rundirsplit)
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		# Loop through runnames
		for n in np.arange(0, len(runnames)):
			# s.find is a boolean function, returns -1 if false
			# cycles through list of runnames, if runname is in .123 file...	
			if s.find(runnames[n]) != -1: 
				dirname = dirnames[n]
				# Rename dir, create nii files
				exphasedir = datadir + '/' + subnum + '/' + dirname
				if not os.path.exists(exphasedir):
					os.rename(rundir, exphasedir)
				# Run dcm2niix to convert
				os.system("dcm2niix -z y -b y -ba y {}".format(exphasedir))
				# find nii file
				src = glob.glob('*.gz')
				# copy file to 'func' or 'anat' folder, rename accordingly
				dst = newstudydir + '/' + dirname + '.nii.gz'
				if not src:  # in case glob doesn't find anything, script continues
					pass
				else:
					shutil.copy2(src[0], dst)
				# find json file (created with dcm2niix)
				src = glob.glob('*.json')
				# copy file to 'func' or 'anat' folder, rename accordingly
				dst = newstudydir + '/' + dirname + '.json'
				if not src:
					pass
				else:
					shutil.copy2(src[0], dst)
