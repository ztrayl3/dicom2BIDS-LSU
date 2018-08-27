# README for LSU BIDSuite.py
------------------------------------------------------------------------------------------------------------------------
### Important notes:

This program was designed for use at the Pennington Biomedical Research Center's Neuroimaging Lab. Results are not guarenteed for other scanners, but with sufficient coding know-how the suite can be modified.

This program is not executable alone. It instead contains several functions that are to be
imported and called in a separate python script. This functionality allows for a wider range
of use for the functions across almost any data set. That being said, in order to run the
functions for all of your participants, arrays and loops must be used.

Import as:
```python
from BIDSuite import *
```

Example:
```python
# you have participants 17121, 17122, and 17123.
# Create an array
A = ["17121", "17122", "17123"]
# then iterate over it in a loop.

for participant in A:
    example_function(participant)
```

This will run the function for each participant in your array

### Requirements:

* linux

* dcm2niix

* python 2.x

* pydeface

* numpy

* csv
----
### Function specific notes and usage:
----
##### create_tree(path, sub_count):
This function creates a directory structure as denoted by the BIDS standard.
By default, this script only creates the core elements of the bids format

**NOTE**

-that additional folders can be added to the function by editing the code

-less than 1000 subjects is assumed

* path = the destination path for directory structure (string)

* sub_count = the number of subjects (int)

----
##### convert(regex, out_path):

This function makes an exact copy of a folder at "out_path" with participant IDs replaced with BIDS format
*Example: 17121 -> sub001*
It is important to note as well that this function does not delete or overwrite anything; it only makes copies.
Again, less than 1000 subjects is assumed.

* regex = the regular expression for your participant IDs (string)

* out_path = the path to the folder being converted (string)

**Note: the function recursively names ALL sub-files and folders containing the participant ID (in the exact-copy directory)**

----
##### organize(base_dir, scan_dir, rnames, dnames, partID, scan_type):
This function takes the dicom data from the MRI scan, converts it to nifti format and stores the resulting files.
It works through reading of the lotus (.123) files within the series (ser#) folders [this actually might not be the case, rather it works by reading the header info from file .123 within the series, which we picked because it looked like a lotus file (.123). This is suboptimal for serieses with under 123 volumes, but could be fixed manuall]. Within those files, if the rname is found that run is renamed with the respective dname (see code for more explanation).

* base_dir = the home folder of the study (example: "../FCTM_S_Data") (string)

* scan_dir = location of extracted MRI scan data (all of the Ser# folders) (string)

* rnames = names found in the lotus (.123) files to be replaces by their index equal in dnames (string array)

* dnames = a list of replacement names for the rnames in the lotus (.123) files (string array)

* partID = the participant ID (example: 17126, string or int)

* scan_type = anatomical or functional MRI data (char, 'a' or 'f')
