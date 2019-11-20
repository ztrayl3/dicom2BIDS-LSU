# Imports
import pydicom
import tarfile
import shutil
import json
import glob
import csv
import sys
import os
if sys.version_info[0] >= 3:
    raise Exception("Must be using Python 2.x")
##########

# functions
def clean(a):  # takes a list of files, returns only those containing MRI data
	for i in a:
		# if folders don't contain Ser (MRI series) subdirectories (and sub-subdirectories in some cases) 
		if not len(glob.glob(os.path.join(i, "Ser*"))) and not len(glob.glob(os.path.join(i, "*", "Ser*"))):
			a.remove(i)  # remove them
			print i + " removed"
	return sorted(a)  # sort it for simplicity

###########

# initial values
already_run = False  # assume first time running script
sub_count = 1
runnames = []
conversion = {}
directories = next(os.walk(os.getcwd()))[1]  # build list of sub folders in the current directory for later iteration
start = os.path.join(os.getcwd(), "BIDS")  # folder to contain all data in BIDS format
try:
	os.makedirs(start)  # make the starting folder
except OSError:
	already_run = True  # if it is already there, prepare to add new folders
################

# remove irrelevant folders and files from iteration to avoid errors
if already_run:  # if not first time, all previous folders "irrelevant"
	print "Pipeline has been run before, ignoring previous subjects."

	# check conversion_key.csv for info on previous folders
	with open('conversion_key.csv', mode='r') as infile:
		reader = csv.reader(infile)
		conversion = {rows[0]:rows[1] for rows in reader}

	# pick up where it left off
	sub_count = conversion[max(conversion, key=lambda key: conversion[key])]  # update sub_count to max where we left off last time
	sub_count = int(sub_count.split('-')[1].lstrip('0')) + 1 # ensure we only have the integer portion of "sub-001" (turn it to 1)
	# also add 1 to sub_count to not overwrite most recent folder

	# run the rest of script off of new, shortened dirs list
	for i in directories:
		if i in conversion:  # if we have already handled directory
			directories.remove(i)  # remove it as to not duplicate

# Ensure we are only working with MRI folders
dirs = clean(directories)
print dirs
print
####################################################################

# Establish list of run names for experiment
for i in dirs:  # for each extracted Pennington data folder (A00-07-4174_E3070_2018Oct02 for example) at the current directory
	for j in os.listdir(i):  # for each series folder within our participant folder (Ser*)
		for k in glob.glob(os.path.join(i, j, "*.MRDC.1")):  # open the first dicom in each series
			dicom = pydicom.dcmread(k).SeriesDescription  # pull out its description
			if not dicom in runnames:  # if we haven't already
				runnames.append(dicom)  # record it as a run name
print "Gathered Run Names:"
for i in sorted(runnames):
	print i
print
#############################################

# build BIDS directory tree for the number of participants present
for i in range(len(dirs)):
	name = "sub-"  # prepare for number padding (to always have 3 digits)
	if sub_count < 100:  # given sub_count = 1
		name = name + '0'  # name = sub-0
		if sub_count < 10:
			name = name + '0'  # name = sub-00
	name = name + str(sub_count)  # name = sub-00x / sub-0xx / sub-xxx
	sub_path = os.path.join(start, name)
	print "Making directory {} for scan {}".format(sub_path, dirs[i])
	os.makedirs(sub_path)  # make ./BIDS/sub-001 folder

	# write original folder and corresponding sub-xxx folder to dictionary and csv for safe keeping
	with open("conversion_key.csv", 'a') as key:
		writer = csv.writer(key)
		writer.writerow([dirs[i], name])
	key.close()
	conversion[dirs[i]] = name

	sub_count = sub_count + 1  # iterate subject counter

	### Add more sub-folders by copying the following line and changing the name to what you want to add ###
	# os.makedirs(os.path.join(sub_path, 'YOUR DESIRED SUB-FOLDER')
	os.makedirs(os.path.join(sub_path, 'func'))  # REQUIRED BY BIDS
	os.makedirs(os.path.join(sub_path, 'anat'))  # REQUIRED BY BIDS
	# insert additional optional folders here

###################################################################

# convert dicoms to nifti format
# output example: 18072_task-AUTOBIO_1_bold.nii.gz (and .json)
for i in dirs:
	targets = []
	destination = "BIDS" + os.sep + conversion[i]
	os.system("dcm2niix -b y -ba y -z y -f %f_task-%p_bold {}".format(i))
	targets.extend(glob.glob(i + os.sep + "*.gz"))
	targets.extend(glob.glob(i + os.sep + "*.json"))
	for j in targets:
		# fix file name formatting messed up by dcm2niix
		k = j.replace(i, conversion[i])  # k now contains corrected name (ex: sub-001/sub-001_task-AUTOBIO1_bold.nii.gz)
		k = k.replace('_', '')
		k = k.replace('task', '_task')
		k = k.replace('bold', '_bold')
		j = j.split(os.sep)[1]
		k = k.split(os.sep)[1]  # remove extra subject id from beginning of j and k ("sub-001/" and "18072/" for example)

		if "SAG_MPRAGE" in j:  # anything relating to anatomical scans
			k = k.split("_")
			k.pop(1)
			k.insert(1, "T1w")
			k[-1] = k[-1][4:]  # remove "bold" from anatomical names
			k = k[0] + '_' + k[1] + k[2]  # name of anatomical scan now T1w not task-SAG_MPRAGE (ex: sub-001_T1w.nii.gz)

			shutil.move(i + os.sep + j, destination + os.sep + "anat")
			os.rename(os.path.join(destination, "anat", j), os.path.join(destination, "anat", k))
			if j[-2] == "gz":  # ensure only touching image file not .json sidecar
				os.system("pydeface {}".format(os.path.join(destination, "anat", k)))  # deface anatomical image for security

		elif "3Plane" in j or "Cal_32Ch_Head" in j:  # discarded by default, can change if they are needed
			os.remove(i + os.sep + j)

		else:  # everything related to functional scans
			if j[-4:] == "json":  # add TaskName attribute to json files
				tn = {"TaskName": k.split('_')[1][5:]}  # TaskName should be task-AUTOBIO1 for example, but without the "task-"
				with open(i + os.sep + j) as f:
					data = json.load(f)
				data.update(tn)
				with open(i + os.sep + j, 'w') as f:
					json.dump(data, f)  # json file now updated, only functional images need this addition

			shutil.move(i + os.sep + j, destination + os.sep + "func")
			os.rename(os.path.join(destination, "func", j), os.path.join(destination, "func", k))
	print i + " ({}) Done".format(conversion[i])
	print
################################
