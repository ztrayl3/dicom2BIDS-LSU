# README for LSU BIDSuite.py
------------------------------------------------------------------------------------------------------------------------
### Important notes:

This program was designed for use with the Pennington Biomedical Research Center's Neuroimaging Lab and their fMRI scanner. Results are not guarenteed for other scanners, but with sufficient coding know-how the suite can be modified.

The BIDSuite will name MRI runs based off of what they were named at the scanner. Whatever run name was enterd for the fMRI protocol is the name of the resulting nifti file.

The pipeline can be run again to add new subjects to the folder structure. This is done through the conversion.csv file (also present to allow validation of subject ID to subject number). DO NOT remove this file at risk of overwriting data. 

### Program requirements:
* python 2.7.x
* pydicom
* dcm2niix
* pydeface

### Before running:
Code assumes that files from the Pennington Scanner have been extracted
EX: example.tgz -> a folder containing MRI series sub-folders (example/Ser1 etc...)


