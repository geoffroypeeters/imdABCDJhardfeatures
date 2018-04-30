# imdABCDJhardfeatures

**Author**: peeters@ircam.fr

**Date**: 2018/04/30

**Description**: A python package to compute TU-Berlin Hard Features as defined in the ABC_DJ H2020 Project (imd stands for Ircam Music Description).


## Content

- imdABCDJhardfeatures.sh: 
	- a bash script that perform mp3 decoding, call C++ executable, call python scripts

- imdABCDJhardfeatures.py
	- main python script that extract all TU-berlin Hard Features
- peeaudiolight.py
	- set of functions to extract HPSS related features
- peeTimbreToolbox.py
	- python version of the TimbreToolbox
- my_tools.py
	- set of tools used by the python version of the TimbreToolbox
- swipep.py
	- fundamental frequency estimation used by the python version of the TimbreToolbox

## Requirements

- Python 2.7.14
	- numpy==1.14.3
	- scipy==1.0.1
	- xmltodict==0.11.0

- ```mpg123```:
	- get mpg123 installed to your platform

- ```imdABCDJ-2.0.0```:
	- proprietary C++ executable from IRCAM that extract beat, key, chord, tags
	- In ircamABCDJhardfeatures.sh, 

## Configuration

In ```ircamABCDJhardfeatures.sh```: 

- set the variable ```MPG123``` to the location where ```mpg123``` is installed
- set the variable ```IMD``` to the location where ````imdABCDJ-2.0.0```` is installed
- set the variable ```TMP_DIR``` to an existing folder where temporary files can be written
- set the variable ```IMDHF```to the location of the python script ```ircamABCDJhardfeatures.py```

## Usage

### Usage 1

As an example, we provide a bash script ```ircamABCDJhardfeatures.sh ``` as example.
	
	ircamABCDJhardfeatures.sh fullPathToAudioFile

### Usage 2

For production, the python script ```imdABCDJhardfeatures.py``` should be used directly. 
This pytho script takes as inputs
	
- ```fullPathToWavFile```: the full path to the decompressed audio file (wav file)
- ```fullPathToXmlFile```: the full path to the XML file as outputed by the C++ executable ```imdABCDJ-2.0.0```
- ```fullPathJsonFile```: the full path to the JSON file in which the results will be written
- ```TmpDir```: an existing folder where temporary results will be written

The command line is then

	imdABCDJhardfeatures.py -a $fullPathToWavFile -x $fullPathToXmlFile -o $fullPathJsonFile --tmpdir $TmpDir

